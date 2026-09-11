from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from backend.database.db import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    reporter_name = Column(String, default="Anonymous Citizen")
    emergency_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    location = Column(String, default="Coordinates unavailable")
    
    # AI-derived triage fields
    severity = Column(String, default="Unknown")    # Low, Medium, High, Critical
    urgency = Column(String, default="Unknown")     # Normal, High, Immediate
    priority = Column(String, default="Unknown")    # P1-Critical, P2-High, P3-Medium, P4-Low
    
    # Orchestrator lifecycle status
    status = Column(String, default="NEW")
    assigned_responder_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)