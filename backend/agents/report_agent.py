import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.incident import Incident
from backend.models.assignment import Assignment
from backend.models.responder import Responder
from backend.models.incident_timeline import IncidentTimeline
from backend.models.agent_action import AgentAction
from backend.models.report import Report
from backend.agents.llm_service import call_llm, clean_json_response

class AIIncidentReportAgent:
    """
    AI Incident Report Agent
    Synthesizes the complete incident lifecycle, timeline logs,
    responder actions, and escalation traces into an executive postmortem report.
    """

    SYSTEM_PROMPT = """
    You are the ResQAgent Post-Incident Review Agent.
    Generate a professional, high-clarity emergency response debrief report.
    Return JSON matching this exact structure:
    {
      "summary": "Concise 2-3 sentence executive debrief describing the emergency, dispatch, escalation (if any), and successful resolution.",
      "key_takeaways": ["Takeaway 1", "Takeaway 2"],
      "agentic_performance_score": "95/100"
    }
    """

    @classmethod
    def generate_report(cls, db: Session, incident_id: int) -> Report:
        # Check if report already exists
        existing = db.query(Report).filter(Report.incident_id == incident_id).first()
        if existing:
            return existing

        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None

        # Fetch assignments
        assignments = (
            db.query(Assignment)
            .filter(Assignment.incident_id == incident_id)
            .order_by(Assignment.assigned_at.asc())
            .all()
        )

        initial_responder_name = "N/A"
        final_responder_name = "N/A"
        escalation_count = max(0, len(assignments) - 1)

        if assignments:
            first_resp = db.query(Responder).filter(Responder.id == assignments[0].responder_id).first()
            if first_resp:
                initial_responder_name = first_resp.name
            
            last_resp = db.query(Responder).filter(Responder.id == assignments[-1].responder_id).first()
            if last_resp:
                final_responder_name = last_resp.name

        # Calculate response time
        response_time = (
            (incident.updated_at - incident.created_at).total_seconds()
            if incident.updated_at and incident.created_at
            else 45.0
        )

        # Timeline entries
        timeline_entries = (
            db.query(IncidentTimeline)
            .filter(IncidentTimeline.incident_id == incident_id)
            .order_by(IncidentTimeline.timestamp.asc())
            .all()
        )
        timeline_summary = "; ".join([f"[{t.actor}] {t.description}" for t in timeline_entries[:6]])

        # Query LLM for debrief synthesis
        prompt = f"""
        Incident ID: #{incident.id}
        Emergency: {incident.emergency_type} ({incident.priority} - {incident.severity})
        Description: {incident.description}
        Location: {incident.location}
        Initial Responder: {initial_responder_name}
        Escalation Count: {escalation_count}
        Final Responder: {final_responder_name}
        Timeline Highlights: {timeline_summary}
        """

        raw_output = call_llm(prompt, system_instruction=cls.SYSTEM_PROMPT)
        parsed = clean_json_response(raw_output) if raw_output else None

        if parsed and "summary" in parsed:
            summary = parsed["summary"]
        else:
            if escalation_count > 0:
                summary = (
                    f"Emergency #{incident.id} ({incident.emergency_type}) was triaged at {incident.priority} priority. "
                    f"Initial unit {initial_responder_name} timed out and the system autonomously escalated and re-routed "
                    f"to {final_responder_name}, who accepted the mission and successfully resolved the incident on scene."
                )
            else:
                summary = (
                    f"Emergency #{incident.id} ({incident.emergency_type}) triaged at {incident.priority} priority. "
                    f"Primary unit {final_responder_name} accepted dispatch immediately and completed assistance."
                )

        full_dossier = {
            "incident_id": f"INC-{incident.id}",
            "emergency_type": incident.emergency_type,
            "priority": incident.priority,
            "severity": incident.severity,
            "location": incident.location,
            "initial_responder": initial_responder_name,
            "final_responder": final_responder_name,
            "escalations_handled": escalation_count,
            "response_time_seconds": round(response_time, 1),
            "final_status": incident.status,
            "executive_summary": summary,
            "cognitive_agent_loop": "PERCEIVE -> REASON -> DECIDE -> ACT -> OBSERVE -> ADAPT",
            "generated_at": datetime.utcnow().isoformat()
        }

        report = Report(
            incident_id=incident.id,
            summary=summary,
            emergency_type=incident.emergency_type,
            severity=incident.severity,
            priority=incident.priority,
            initial_responder=initial_responder_name,
            final_responder=final_responder_name,
            escalation_count=escalation_count,
            response_time_seconds=response_time,
            final_status=incident.status,
            full_report_json=json.dumps(full_dossier, indent=2)
        )
        db.add(report)

        # Record timeline event
        db.add(IncidentTimeline(
            incident_id=incident.id,
            event_type="REPORT_GENERATED",
            description=f"AI Incident Report Agent synthesized comprehensive debrief (INC-{incident.id}).",
            actor="Report Agent"
        ))

        db.commit()
        db.refresh(report)
        return report
