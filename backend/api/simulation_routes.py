from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database.db import get_db
from backend.models.user import User
from backend.models.incident import Incident
from backend.models.assignment import Assignment
from backend.models.responder import Responder
from backend.models.incident_timeline import IncidentTimeline
from backend.models.agent_action import AgentAction
from backend.models.notification import Notification
from backend.models.report import Report
from backend.core.dependencies import require_dispatcher, require_admin

router = APIRouter()

@router.post("/reset")
def reset_simulation_state(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only demonstration reset.
    Clears test incidents, assignments, notifications, actions, and reports.
    Preserves administrator accounts.
    """
    db.query(Report).delete()
    db.query(AgentAction).delete()
    db.query(IncidentTimeline).delete()
    db.query(Notification).delete()
    db.query(Assignment).delete()
    db.query(Incident).delete()
    db.commit()
    
    return {
        "status": "success",
        "message": "Operational incidents, assignments, and agent logs cleared."
    }

@router.post("/timeout/{incident_id}")
def simulate_responder_timeout(
    incident_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db)
):
    """
    Dispatcher/Admin endpoint to simulate SLA timeout.
    Activates Monitoring Agent -> Escalation Agent loop.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    assignment = (
        db.query(Assignment)
        .filter(Assignment.incident_id == incident_id, Assignment.assignment_status == "PENDING")
        .order_by(Assignment.assigned_at.desc())
        .first()
    )
    if not assignment:
        raise HTTPException(
            status_code=400,
            detail="No pending assignment found to timeout for this incident."
        )

    responder = db.query(Responder).filter(Responder.id == assignment.responder_id).first()
    
    assignment.assignment_status = "TIMEOUT"
    assignment.responded_at = datetime.utcnow()
    assignment.notes = f"SLA Breached: Responder did not acknowledge within 5s timeout window (Simulated by {current_user.name})."
    
    if responder:
        responder.availability = "AVAILABLE"
        responder.active_incident_id = None
        
    incident.status = "NO_RESPONSE"
    
    event = IncidentTimeline(
        incident_id=incident.id,
        event_type="SLA_TIMEOUT_EXPIRED",
        description=f"Monitoring Agent: SLA expired (5s) for {responder.name if responder else 'Responder'}. Escalating.",
        actor="Monitoring Agent"
    )
    db.add(event)
    db.commit()

    from backend.agents.orchestrator import run_escalation_cycle
    background_tasks.add_task(
        run_escalation_cycle,
        incident.id,
        reason=f"SLA Timeout: Responder {responder.name if responder else 'Unknown'} failed to respond within time limit"
    )

    return {
        "status": "escalation_triggered",
        "incident_id": incident_id,
        "timed_out_responder": responder.name if responder else "Unknown",
        "message": "SLA timeout breach simulated. Escalation Agent activated to reassign candidate."
    }
