import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models.incident import Incident
from backend.models.assignment import Assignment

class MonitoringAgent:
    """
    Monitoring Agent
    Monitors incident SLA timers, responder acknowledgment windows,
    and assistance progress. Flags anomalies and timeout breaches.
    """

    DEFAULT_TIMEOUT_SECONDS = int(os.getenv("RESPONDER_TIMEOUT_SECONDS", "5"))

    @classmethod
    def check_assignment_health(
        cls,
        db: Session,
        incident_id: int,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    ) -> Dict[str, Any]:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return {"status": "ERROR", "reason": "Incident not found"}

        latest_assignment = (
            db.query(Assignment)
            .filter(Assignment.incident_id == incident_id)
            .order_by(Assignment.assigned_at.desc())
            .first()
        )

        if not latest_assignment:
            return {"status": "UNASSIGNED", "reason": "No active assignments"}

        if latest_assignment.assignment_status == "ACCEPTED":
            return {
                "status": "HEALTHY",
                "assignment_id": latest_assignment.id,
                "responder_id": latest_assignment.responder_id,
                "message": "Responder accepted and active."
            }

        if latest_assignment.assignment_status == "PENDING":
            elapsed = (datetime.utcnow() - latest_assignment.assigned_at).total_seconds()
            if elapsed > timeout_seconds:
                return {
                    "status": "BREACH_TIMEOUT",
                    "assignment_id": latest_assignment.id,
                    "responder_id": latest_assignment.responder_id,
                    "elapsed_seconds": round(elapsed, 1),
                    "reason": f"Responder failed to respond within {timeout_seconds}s SLA window."
                }
            return {
                "status": "WAITING",
                "assignment_id": latest_assignment.id,
                "responder_id": latest_assignment.responder_id,
                "elapsed_seconds": round(elapsed, 1),
                "remaining_seconds": max(0, round(timeout_seconds - elapsed, 1))
            }

        return {
            "status": latest_assignment.assignment_status,
            "assignment_id": latest_assignment.id,
            "responder_id": latest_assignment.responder_id
        }
