from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    incident_id: int
    recipient_type: str
    recipient_name: str
    message: str
    channel: Optional[str] = "IN_APP"

class NotificationResponse(BaseModel):
    id: int
    incident_id: int
    recipient_type: str
    recipient_name: str
    message: str
    channel: str
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True
