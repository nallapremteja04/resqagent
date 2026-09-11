import json
from typing import Optional
from sqlalchemy.orm import Session

from backend.database.db import SessionLocal
from backend.models.incident import Incident
from backend.models.assignment import Assignment
from backend.models.agent_action import AgentAction
from backend.models.incident_timeline import IncidentTimeline
from backend.agents.analysis_agent import EmergencyAnalysisAgent
from backend.agents.selection_agent import ResponderSelectionAgent
from backend.agents.communication_agent import CommunicationAgent
from backend.agents.escalation_agent import EscalationAgent
from backend.agents.report_agent import AIIncidentReportAgent

class AgentOrchestrator:
    """
    Agent Orchestrator
    Manages the multi-agent state machine and coordinates the cognitive loop:
    PERCEIVE -> REASON -> DECIDE -> ACT -> OBSERVE -> ADAPT -> REPORT
    """

    @classmethod
    def process_new_incident(cls, incident_id: int, db: Optional[Session] = None):
        """
        Executes the initial autonomous flow:
        NEW -> ANALYZING -> ANALYZED -> RESPONDER_SEARCH -> RESPONDER_ASSIGNED -> WAITING_FOR_RESPONSE
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
            if not incident:
                return

            # STEP 1: PERCEIVE & REASON -> Emergency Analysis Agent
            incident.status = "ANALYZING"
            db.commit()

            triage = EmergencyAnalysisAgent.analyze(
                description=incident.description,
                declared_type=incident.emergency_type,
                location=incident.location
            )

            incident.emergency_type = triage.get("emergency_type", incident.emergency_type)
            incident.severity = triage.get("severity", "Medium")
            incident.urgency = triage.get("urgency", "Normal")
            incident.priority = triage.get("priority", "P2-High")
            incident.status = "ANALYZED"
            db.commit()

            # Log Analysis Agent Action
            action_analysis = AgentAction(
                incident_id=incident.id,
                agent_name="EmergencyAnalysisAgent",
                action_type="CLASSIFICATION_TRIAGE",
                input_data=json.dumps({
                    "description": incident.description,
                    "location": incident.location
                }),
                output_data=json.dumps(triage),
                reasoning=triage.get("reason", "Structured emergency parameters determined.")
            )
            db.add(action_analysis)

            # Log Timeline
            db.add(IncidentTimeline(
                incident_id=incident.id,
                event_type="AI_TRIAGE_COMPLETED",
                description=f"Triaged as {incident.priority} ({incident.severity} severity). Type: {incident.emergency_type}.",
                actor="Analysis Agent"
            ))
            db.commit()

            # STEP 2: DECIDE -> Responder Selection Agent
            incident.status = "RESPONDER_SEARCH"
            db.commit()

            selection_result = ResponderSelectionAgent.select_best_responder(
                db=db,
                emergency_type=incident.emergency_type,
                priority=incident.priority,
                exclude_responder_ids=[]
            )

            selected_responder = selection_result.get("selected_responder")
            if not selected_responder:
                incident.status = "UNABLE_TO_ASSIGN"
                db.commit()
                db.add(IncidentTimeline(
                    incident_id=incident.id,
                    event_type="DISPATCH_FAILED",
                    description="No available responders in pool. Alerting human dispatch.",
                    actor="Selection Agent"
                ))
                db.commit()
                return

            # Log Selection Agent Action
            action_selection = AgentAction(
                incident_id=incident.id,
                agent_name="ResponderSelectionAgent",
                action_type="RESPONDER_SELECTION",
                input_data=json.dumps({
                    "emergency_type": incident.emergency_type,
                    "priority": incident.priority
                }),
                output_data=json.dumps({
                    "selected": selected_responder.name,
                    "distance_km": selected_responder.distance,
                    "ranked_candidates": selection_result.get("ranked_candidates", [])
                }),
                reasoning=selection_result.get("reason", "Proximity and specialization match.")
            )
            db.add(action_selection)

            # Create Assignment
            assignment = Assignment(
                incident_id=incident.id,
                responder_id=selected_responder.id,
                assignment_status="PENDING",
                attempt_number=1,
                notes="Primary automated dispatch."
            )
            db.add(assignment)

            # Update status
            selected_responder.availability = "PENDING_CONFIRMATION"
            selected_responder.active_incident_id = incident.id
            incident.assigned_responder_id = selected_responder.id
            incident.status = "WAITING_FOR_RESPONSE"
            
            db.add(IncidentTimeline(
                incident_id=incident.id,
                event_type="DISPATCH_SENT",
                description=f"Assigned to {selected_responder.name} ({selected_responder.role}, {selected_responder.distance} km away).",
                actor="Orchestrator"
            ))
            db.commit()

            # STEP 3: ACT -> Communication Agent
            notifications = CommunicationAgent.dispatch_initial_alerts(
                db=db,
                incident=incident,
                responder=selected_responder
            )

            action_comm = AgentAction(
                incident_id=incident.id,
                agent_name="CommunicationAgent",
                action_type="STAKEHOLDER_BROADCAST",
                input_data=json.dumps({"responder": selected_responder.name, "priority": incident.priority}),
                output_data=json.dumps({"dispatched_count": len(notifications)}),
                reasoning=f"Alerted Responder {selected_responder.name}, Citizen, Dispatch, and Emergency Facilities."
            )
            db.add(action_comm)
            db.commit()

        finally:
            if should_close:
                db.close()

    @classmethod
    def handle_escalation(cls, incident_id: int, reason: str = "Responder SLA timeout expired", db: Optional[Session] = None):
        """
        Executes the adaptive failure path:
        WAITING_FOR_RESPONSE -> NO_RESPONSE -> ESCALATION -> RESPONDER_SEARCH -> NEW_RESPONDER_ASSIGNED
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            return EscalationAgent.execute_escalation(db=db, incident_id=incident_id, reason=reason)
        finally:
            if should_close:
                db.close()

    @classmethod
    def generate_report(cls, incident_id: int, db: Optional[Session] = None):
        """
        Triggers post-incident report synthesis
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            return AIIncidentReportAgent.generate_report(db=db, incident_id=incident_id)
        finally:
            if should_close:
                db.close()

# Helper aliases for background task hooks
def run_orchestrator_pipeline(incident_id: int):
    AgentOrchestrator.process_new_incident(incident_id)

def run_escalation_cycle(incident_id: int, reason: str = "Responder declined"):
    AgentOrchestrator.handle_escalation(incident_id, reason=reason)

def generate_incident_report(incident_id: int, db: Optional[Session] = None):
    return AgentOrchestrator.generate_report(incident_id, db=db)
