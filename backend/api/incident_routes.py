from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database.db import get_db
from backend.models.user import User
from backend.models.incident import Incident
from backend.models.incident_timeline import IncidentTimeline
from backend.models.agent_action import AgentAction
from backend.models.notification import Notification
from backend.core.dependencies import (
    get_current_user,
    require_authenticated_user,
    require_dispatcher
)
from backend.schemas.incident_schema import IncidentCreate, IncidentStatusUpdate, IncidentResponse
from backend.schemas.timeline_schema import TimelineEventResponse
from backend.schemas.agent_action_schema import AgentActionResponse
from backend.schemas.notification_schema import NotificationResponse

router = APIRouter()

def verify_incident_access(incident: Incident, current_user: User):
    """
    Enforces privacy boundary: Citizens can only access incidents they reported.
    Dispatchers and Administrators have operational visibility across all incidents.
    """
    if current_user.role == "citizen" and incident.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view your own emergency incidents."
        )

@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident_in: IncidentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Creates an emergency incident.
    Automatically binds the incident to the authenticated user's ID and name.
    """
    incident = Incident(
        user_id=current_user.id,
        reporter_name=current_user.name,
        emergency_type=incident_in.emergency_type,
        description=incident_in.description,
        location=incident_in.location or current_user.location or "Sector 5, Downtown",
        status="NEW"
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Log initial timeline event
    initial_event = IncidentTimeline(
        incident_id=incident.id,
        event_type="INCIDENT_REPORTED",
        description=f"Distress report submitted: {incident.emergency_type} - '{incident.description[:60]}...'",
        actor=incident.reporter_name
    )
    db.add(initial_event)
    db.commit()

    # Trigger Agent Orchestrator in background
    try:
        from backend.agents.orchestrator import run_orchestrator_pipeline
        background_tasks.add_task(run_orchestrator_pipeline, incident.id)
    except ImportError:
        pass

    return incident

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Lists incidents based on user role:
    - Citizens: Only their own submitted incidents.
    - Dispatchers / Admins / Responders: All operational incidents.
    """
    query = db.query(Incident)

    if current_user.role == "citizen":
        query = query.filter(Incident.user_id == current_user.id)
        
    if status_filter:
        query = query.filter(Incident.status == status_filter.upper())
    if priority:
        query = query.filter(Incident.priority == priority)

    return query.order_by(Incident.created_at.desc()).all()

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Fetches details of a specific incident with access control."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    verify_incident_access(incident, current_user)
    return incident

@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: int,
    status_in: IncidentStatusUpdate,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db)
):
    """Dispatcher/Admin endpoint to manually override incident status."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    old_status = incident.status
    incident.status = status_in.status.upper()
    incident.updated_at = datetime.utcnow()
    
    event = IncidentTimeline(
        incident_id=incident.id,
        event_type="STATUS_CHANGED",
        description=f"Incident status changed from {old_status} to {incident.status} by {current_user.name}",
        actor=current_user.name
    )
    db.add(event)
    db.commit()
    db.refresh(incident)
    return incident

@router.get("/{incident_id}/timeline", response_model=List[TimelineEventResponse])
def get_incident_timeline(
    incident_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Chronological event audit trail for an incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    verify_incident_access(incident, current_user)

    return (
        db.query(IncidentTimeline)
        .filter(IncidentTimeline.incident_id == incident_id)
        .order_by(IncidentTimeline.timestamp.asc())
        .all()
    )

@router.get("/{incident_id}/actions", response_model=List[AgentActionResponse])
def get_incident_agent_actions(
    incident_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """AI agent cognitive actions trace."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    verify_incident_access(incident, current_user)

    return (
        db.query(AgentAction)
        .filter(AgentAction.incident_id == incident_id)
        .order_by(AgentAction.created_at.asc())
        .all()
    )

@router.get("/{incident_id}/notifications", response_model=List[NotificationResponse])
def get_incident_notifications(
    incident_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Multi-stakeholder alerts dispatched for this incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    verify_incident_access(incident, current_user)

    return (
        db.query(Notification)
        .filter(Notification.incident_id == incident_id)
        .order_by(Notification.sent_at.desc())
        .all()
    )