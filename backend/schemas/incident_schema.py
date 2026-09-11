from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IncidentCreate(BaseModel):
    user_id: Optional[int] = None
    reporter_name: Optional[str] = "Anonymous Citizen"
    emergency_type: str
    description: str
    location: Optional[str] = "Sector 5, Downtown"

class IncidentStatusUpdate(BaseModel):
    status: str

class IncidentResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    reporter_name: Optional[str] = None
    emergency_type: str
    description: str
    location: Optional[str] = None
    severity: Optional[str] = "Unknown"
    urgency: Optional[str] = "Unknown"
    priority: Optional[str] = "Unknown"
    status: str
    assigned_responder_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True