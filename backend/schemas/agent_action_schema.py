from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AgentActionCreate(BaseModel):
    incident_id: int
    agent_name: str
    action_type: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    reasoning: Optional[str] = None

class AgentActionResponse(BaseModel):
    id: int
    incident_id: int
    agent_name: str
    action_type: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    reasoning: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
