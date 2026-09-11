from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database.db import get_db
from backend.models.user import User
from backend.models.report import Report
from backend.models.incident import Incident
from backend.core.dependencies import require_authenticated_user, require_dispatcher
from backend.schemas.report_schema import ReportResponse

router = APIRouter()

@router.get("/", response_model=List[ReportResponse])
def get_all_reports(
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db)
):
    """Dispatcher and Admin overview of all synthesized incident reports."""
    return db.query(Report).order_by(Report.created_at.desc()).all()

@router.get("/{incident_id}", response_model=ReportResponse)
def get_incident_report(
    incident_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Fetches postmortem report for an incident with citizen ownership validation."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if current_user.role == "citizen" and incident.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view reports for your own incidents."
        )

    report = db.query(Report).filter(Report.incident_id == incident_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for this incident")
    return report

@router.post("/{incident_id}/generate", response_model=ReportResponse)
def trigger_generate_report(
    incident_id: int,
    current_user: User = Depends(require_dispatcher),
    db: Session = Depends(get_db)
):
    """Dispatcher/Admin on-demand trigger to synthesize report."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    from backend.agents.orchestrator import generate_incident_report
    report = generate_incident_report(incident_id, db=db)
    if not report:
        raise HTTPException(status_code=500, detail="Failed to synthesize incident report")
    return report
