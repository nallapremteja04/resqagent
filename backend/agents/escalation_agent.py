import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.models.incident import Incident
from backend.models.assignment import Assignment
from backend.models.responder import Responder
from backend.models.agent_action import AgentAction
from backend.models.incident_timeline import IncidentTimeline
from backend.agents.selection_agent import ResponderSelectionAgent
from backend.agents.communication_agent import CommunicationAgent

class EscalationAgent:
    """
    Escalation Agent
    Activated when an assigned responder fails to acknowledge within SLA or declines.
    Autonomously adapts the response plan:
    1. Blacklists non-responsive/declined responder for this incident
    2. Elevates priority if multiple failures occur
    3. Re-engages ResponderSelectionAgent to assign the next best responder
    4. Triggers CommunicationAgent for re-routed dispatch
    5. Logs cognitive reasoning
    """

    MAX_ESCALATION_ATTEMPTS = 3

    @classmethod
    def execute_escalation(
        cls,
        db: Session,
        incident_id: int,
        reason: str = "Responder failed to acknowledge within SLA timeout"
    ) -> Dict[str, Any]:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return {"status": "ERROR", "message": "Incident not found"}

        # Gather past assignments to build blacklist
        past_assignments = (
            db.query(Assignment)
            .filter(Assignment.incident_id == incident_id)
            .all()
        )
        excluded_ids = [a.responder_id for a in past_assignments]
        attempt_number = len(past_assignments) + 1

        last_assignment = past_assignments[-1] if past_assignments else None
        failed_responder_name = "Assigned Unit"
        if last_assignment:
            failed_resp = db.query(Responder).filter(Responder.id == last_assignment.responder_id).first()
            if failed_resp:
                failed_responder_name = failed_resp.name

        # Enforce safety guard: if attempts exceed max, escalate directly to Central Human Dispatch
        if attempt_number > cls.MAX_ESCALATION_ATTEMPTS:
            incident.status = "ESCALATED_TO_DISPATCH"
            db.commit()
            
            action = AgentAction(
                incident_id=incident.id,
                agent_name="EscalationAgent",
                action_type="MAX_ESCALATION_EXCEEDED",
                input_data=json.dumps({"attempt": attempt_number, "reason": reason}),
                output_data=json.dumps({"action": "MANUAL_DISPATCH_TAKEOVER"}),
                reasoning=f"Exceeded {cls.MAX_ESCALATION_ATTEMPTS} autonomous reassignment attempts. Transferred to Human Dispatch."
            )
            db.add(action)
            db.commit()
            return {"status": "ESCALATED_TO_DISPATCH", "message": "Manual dispatch required."}

        # 1. Adapt state to RESPONDER_SEARCH
        incident.status = "RESPONDER_SEARCH"
        db.commit()

        # 2. Select replacement candidate
        selection_result = ResponderSelectionAgent.select_best_responder(
            db=db,
            emergency_type=incident.emergency_type,
            priority=incident.priority,
            exclude_responder_ids=excluded_ids
        )

        new_responder = selection_result.get("selected_responder")
        if not new_responder:
            incident.status = "UNABLE_TO_ASSIGN"
            db.commit()
            return {"status": "UNABLE_TO_ASSIGN", "reason": "No remaining available responders."}

        # 3. Create new assignment
        new_assignment = Assignment(
            incident_id=incident.id,
            responder_id=new_responder.id,
            assignment_status="PENDING",
            attempt_number=attempt_number,
            notes=f"Escalation Attempt #{attempt_number}. Reassigned from {failed_responder_name}."
        )
        db.add(new_assignment)

        # Update responder and incident
        new_responder.availability = "PENDING_CONFIRMATION"
        new_responder.active_incident_id = incident.id
        incident.assigned_responder_id = new_responder.id
        incident.status = "RESPONDER_ASSIGNED"
        db.commit()

        # 4. Record cognitive action
        action_log = AgentAction(
            incident_id=incident.id,
            agent_name="EscalationAgent",
            action_type="ADAPTIVE_REASSIGNMENT",
            input_data=json.dumps({
                "failed_unit": failed_responder_name,
                "reason": reason,
                "attempt": attempt_number,
                "excluded_units": excluded_ids
            }),
            output_data=json.dumps({
                "reassigned_unit": new_responder.name,
                "distance_km": new_responder.distance,
                "specialization": new_responder.specialization
            }),
            reasoning=(
                f"Adaptive recovery: Unit '{failed_responder_name}' dropped out ({reason}). "
                f"Escalation Agent searched pool excluding {excluded_ids} and selected "
                f"'{new_responder.name}' ({new_responder.distance} km away)."
            )
        )
        db.add(action_log)

        # 5. Record timeline
        timeline_log = IncidentTimeline(
            incident_id=incident.id,
            event_type="AUTONOMOUS_ESCALATION",
            description=f"Escalated: {failed_responder_name} dropped. New unit {new_responder.name} assigned.",
            actor="Escalation Agent"
        )
        db.add(timeline_log)
        db.commit()

        # 6. Dispatch targeted re-routing communications
        CommunicationAgent.dispatch_escalation_alerts(
            db=db,
            incident=incident,
            new_responder=new_responder,
            failed_responder_name=failed_responder_name,
            reason=reason
        )

        return {
            "status": "REASSIGNED",
            "attempt": attempt_number,
            "failed_responder": failed_responder_name,
            "new_responder": new_responder.name,
            "new_assignment_id": new_assignment.id
        }
