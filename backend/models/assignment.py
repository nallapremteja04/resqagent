from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from backend.database.db import Base

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    responder_id = Column(Integer, ForeignKey("responders.id"), nullable=False)
    
    # Status: PENDING, ACCEPTED, REJECTED, TIMEOUT, EN_ROUTE, ON_SCENE, COMPLETED
    assignment_status = Column(String, default="PENDING")
    attempt_number = Column(Integer, default=1)
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)