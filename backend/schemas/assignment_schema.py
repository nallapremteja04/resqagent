from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AssignmentCreate(BaseModel):
    incident_id: int
    responder_id: int
    assignment_status: Optional[str] = "PENDING"
    notes: Optional[str] = None

class AssignmentResponseUpdate(BaseModel):
    status: str  # ACCEPTED, REJECTED, EN_ROUTE, ON_SCENE, COMPLETED
    notes: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    incident_id: int
    responder_id: int
    assignment_status: str
    attempt_number: int
    assigned_at: datetime
    responded_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
