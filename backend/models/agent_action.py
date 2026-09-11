from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from backend.database.db import Base

class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    
    agent_name = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    input_data = Column(Text, nullable=True)     # JSON string of agent perception
    output_data = Column(Text, nullable=True)    # JSON string of agent decision
    reasoning = Column(Text, nullable=True)      # Human-readable justification
    created_at = Column(DateTime, default=datetime.utcnow)
