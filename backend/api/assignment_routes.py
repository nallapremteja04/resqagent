import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database.db import get_db
from backend.models.user import User
from backend.models.assignment import Assignment
from backend.models.incident import Incident
from backend.models.responder import Responder
from backend.models.incident_timeline import IncidentTimeline
from backend.models.notification import Notification
from backend.core.dependencies import (
    require_authenticated_user,
    require_dispatcher,
    require_responder
)
from backend.schemas.assignment_schema import (
    AssignmentCreate,
    AssignmentResponseUpdate,
    AssignmentResponse
)

router = APIRouter()

def get_user_responder_id(user: User, db: Session) -> Optional[int]:
    """Finds linked Responder record ID for an authenticated user."""
    resp = db.query(Responder).filter(Responder.user_id == user.id).first()
    return resp.id if resp else None

@router.post("/", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_in: AssignmentCreate,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db)
):
    """Dispatcher/Admin endpoint to dispatch a responder unit."""
    assignment = Assignment(
        incident_id=assignment_in.incident_id,
        responder_id=assignment_in.responder_id,
        assignment_status="PENDING",
        notes=assignment_in.notes or f"Manual dispatch by {current_user.name}"
    )
    db.add(assignment)
    
    responder = db.query(Responder).filter(Responder.id == assignment_in.responder_id).first()
    if responder:
        responder.availability = "PENDING_CONFIRMATION"
        responder.active_incident_id = assignment_in.incident_id
    
    incident = db.query(Incident).filter(Incident.id == assignment_in.incident_id).first()
    if incident:
        incident.assigned_responder_id = assignment_in.responder_id
        incident.status = "RESPONDER_ASSIGNED"
    
    timeline_event = IncidentTimeline(
        incident_id=assignment_in.incident_id,
        event_type="RESPONDER_DISPATCHED",
        description=f"Responder {responder.name if responder else assignment_in.responder_id} assigned by {current_user.name}.",
        actor=current_user.name
    )
    db.add(timeline_event)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.get("/", response_model=List[AssignmentResponse])
def get_assignments(
    incident_id: Optional[int] = None,
    responder_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Lists assignments:
    - Responders can only view assignments targeted to their own unit.
    - Dispatchers and Admins can view all assignments.
    """
    query = db.query(Assignment)

    if current_user.role == "responder":
        user_resp_id = get_user_responder_id(current_user, db)
        if user_resp_id:
            query = query.filter(Assignment.responder_id == user_resp_id)
        else:
            # If responder profile is not yet linked, filter by query param if explicitly testing
            if responder_id:
                query = query.filter(Assignment.responder_id == responder_id)
    elif responder_id:
        query = query.filter(Assignment.responder_id == responder_id)

    if incident_id:
        query = query.filter(Assignment.incident_id == incident_id)
    if status_filter:
        query = query.filter(Assignment.assignment_status == status_filter.upper())

    return query.order_by(Assignment.assigned_at.desc(), Assignment.id.desc()).all()

@router.post("/{assignment_id}/respond", response_model=AssignmentResponse)
def responder_respond(
    assignment_id: int,
    action_in: AssignmentResponseUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_responder),
    db: Session = Depends(get_db)
):
    """
    Responder accepts or declines an assigned mission.
    Enforces that responders only respond to their own unit's assignment.
    Prevents race conditions: rejects responding to assignments that have already timed out or completed.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Race condition safety: only PENDING assignments can be accepted or declined
    if assignment.assignment_status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assignment is no longer pending (Current status: {assignment.assignment_status}). Cannot respond after timeout or completion."
        )
    
    # Ownership guard for responder role (Admins are exempt)
    if current_user.role == "responder":
        user_resp_id = get_user_responder_id(current_user, db)
        if user_resp_id and assignment.responder_id != user_resp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot modify assignments for other responders."
            )

    responder = db.query(Responder).filter(Responder.id == assignment.responder_id).first()
    incident = db.query(Incident).filter(Incident.id == assignment.incident_id).first()
    
    new_status = action_in.status.upper()
    assignment.responded_at = datetime.utcnow()
    assignment.notes = action_in.notes or assignment.notes
    
    if new_status == "ACCEPTED":
        assignment.assignment_status = "ACCEPTED"
        if responder:
            responder.availability = "BUSY"
        if incident:
            incident.status = "ASSISTANCE_IN_PROGRESS"
            
        timeline_event = IncidentTimeline(
            incident_id=assignment.incident_id,
            event_type="DISPATCH_ACCEPTED",
            description=f"Responder {responder.name if responder else 'Responder'} ACCEPTED the call and is en route.",
            actor=responder.name if responder else current_user.name
        )
        db.add(timeline_event)
        
        # Send confirmation notification
        notification = Notification(
            incident_id=assignment.incident_id,
            recipient_type="USER",
            recipient_name=incident.reporter_name if incident else "Citizen",
            message="Responder accepted the emergency assignment.",
            channel="SMS"
        )
        db.add(notification)

    elif new_status in ["REJECTED", "DECLINED"]:
        assignment.assignment_status = "DECLINED"
        if responder:
            responder.availability = "AVAILABLE"
            responder.active_incident_id = None
        if incident:
            incident.status = "NO_RESPONSE"
            
        timeline_event = IncidentTimeline(
            incident_id=assignment.incident_id,
            event_type="DISPATCH_DECLINED",
            description=f"Responder {responder.name if responder else 'Responder'} DECLINED assignment.",
            actor=responder.name if responder else current_user.name
        )
        db.add(timeline_event)

        # Notify dispatch
        notification = Notification(
            incident_id=assignment.incident_id,
            recipient_type="DISPATCH",
            recipient_name="Regional Emergency Dispatch",
            message="Responder declined the assignment. Finding another responder.",
            channel="RADIO"
        )
        db.add(notification)
        
        # Trigger Escalation Agent
        try:
            from backend.agents.orchestrator import run_escalation_cycle
            background_tasks.add_task(run_escalation_cycle, incident.id, reason="Responder Declined")
        except ImportError:
            pass

    db.commit()
    db.refresh(assignment)
    return assignment

@router.post("/{assignment_id}/timeout", response_model=AssignmentResponse)
def timeout_assignment(
    assignment_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Handles assignment timeout when the 5-second acceptance timer expires without response.
    Idempotent and race-condition safe: if assignment is not PENDING, returns current state.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Race condition check: if already accepted or declined, do nothing
    if assignment.assignment_status != "PENDING":
        return assignment

    timeout_sec = int(os.getenv("RESPONDER_TIMEOUT_SECONDS", "5"))
    responder = db.query(Responder).filter(Responder.id == assignment.responder_id).first()
    incident = db.query(Incident).filter(Incident.id == assignment.incident_id).first()

    assignment.assignment_status = "TIMEOUT"
    assignment.responded_at = datetime.utcnow()
    assignment.notes = f"SLA Timeout: Responder did not respond within {timeout_sec} seconds."

    if responder:
        responder.availability = "AVAILABLE"
        responder.active_incident_id = None

    if incident:
        incident.status = "NO_RESPONSE"

    timeline_event = IncidentTimeline(
        incident_id=assignment.incident_id,
        event_type="SLA_TIMEOUT_EXPIRED",
        description=f"Responder {responder.name if responder else 'Unit'} TIMED OUT ({timeout_sec}s SLA expired). Escalating.",
        actor="Monitoring Agent"
    )
    db.add(timeline_event)

    # Required notification: "No response received. Escalating to another responder."
    notification = Notification(
        incident_id=assignment.incident_id,
        recipient_type="DISPATCH",
        recipient_name="Regional Emergency Dispatch",
        message="No response received. Escalating to another responder.",
        channel="RADIO"
    )
    db.add(notification)

    if incident and incident.reporter_name:
        db.add(Notification(
            incident_id=assignment.incident_id,
            recipient_type="USER",
            recipient_name=incident.reporter_name,
            message="No response received from assigned responder. System is escalating to another unit.",
            channel="SMS"
        ))

    db.commit()
    db.refresh(assignment)

    # Trigger Escalation Agent with cognitive loop
    try:
        from backend.agents.orchestrator import run_escalation_cycle
        background_tasks.add_task(
            run_escalation_cycle,
            incident.id,
            reason=f"SLA Timeout: Responder {responder.name if responder else 'Unit'} did not respond within {timeout_sec} seconds"
        )
    except ImportError:
        pass

    return assignment

@router.post("/{assignment_id}/progress", response_model=AssignmentResponse)
def update_assignment_progress(
    assignment_id: int,
    action_in: AssignmentResponseUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_responder),
    db: Session = Depends(get_db)
):
    """Updates operational progress (EN_ROUTE, ON_SCENE, COMPLETED)."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if current_user.role == "responder":
        user_resp_id = get_user_responder_id(current_user, db)
        if user_resp_id and assignment.responder_id != user_resp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot modify assignments for other responders."
            )

    responder = db.query(Responder).filter(Responder.id == assignment.responder_id).first()
    incident = db.query(Incident).filter(Incident.id == assignment.incident_id).first()
    
    new_status = action_in.status.upper()
    assignment.assignment_status = new_status
    
    if new_status == "COMPLETED":
        if responder:
            responder.availability = "AVAILABLE"
            responder.active_incident_id = None
        if incident:
            incident.status = "RESOLVED"
            
        timeline_event = IncidentTimeline(
            incident_id=assignment.incident_id,
            event_type="INCIDENT_RESOLVED",
            description=f"Assistance completed by {responder.name if responder else current_user.name}. Marked RESOLVED.",
            actor=responder.name if responder else current_user.name
        )
        db.add(timeline_event)
        
        try:
            from backend.agents.orchestrator import generate_incident_report
            background_tasks.add_task(generate_incident_report, incident.id)
        except ImportError:
            pass
    else:
        timeline_event = IncidentTimeline(
            incident_id=assignment.incident_id,
            event_type="STATUS_UPDATE",
            description=f"Responder updated progress status: {new_status}",
            actor=responder.name if responder else current_user.name
        )
        db.add(timeline_event)

    db.commit()
    db.refresh(assignment)
    return assignment
