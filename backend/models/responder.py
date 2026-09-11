from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from backend.database.db import Base

class Responder(Base):
    __tablename__ = "responders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    specialization = Column(String, default="General")
    availability = Column(String, default="AVAILABLE")  # AVAILABLE, BUSY, OFFLINE, PENDING_CONFIRMATION
    distance = Column(Float, default=1.0)  # Simulated distance in km
    phone = Column(String, nullable=True)
    current_location = Column(String, default="Central Station")
    active_incident_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)