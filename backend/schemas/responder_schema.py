from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResponderCreate(BaseModel):
    name: str
    role: str
    specialization: Optional[str] = "General"
    availability: Optional[str] = "AVAILABLE"
    distance: Optional[float] = 1.0
    phone: Optional[str] = None
    current_location: Optional[str] = "Central Station"

class ResponderStatusUpdate(BaseModel):
    availability: str  # AVAILABLE, BUSY, OFFLINE

class ResponderResponse(BaseModel):
    id: int
    name: str
    role: str
    specialization: str
    availability: str
    distance: float
    phone: Optional[str] = None
    current_location: Optional[str] = None
    active_incident_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True