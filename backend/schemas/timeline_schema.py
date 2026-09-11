from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TimelineEventCreate(BaseModel):
    incident_id: int
    event_type: str
    description: str
    actor: Optional[str] = "System"

class TimelineEventResponse(BaseModel):
    id: int
    incident_id: int
    event_type: str
    description: str
    actor: str
    timestamp: datetime

    class Config:
        from_attributes = True
