from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportResponse(BaseModel):
    id: int
    incident_id: int
    summary: str
    emergency_type: str
    severity: str
    priority: str
    initial_responder: Optional[str] = None
    final_responder: Optional[str] = None
    escalation_count: int
    response_time_seconds: float
    final_status: str
    full_report_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
