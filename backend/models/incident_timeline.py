from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from backend.database.db import Base

class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    
    event_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    actor = Column(String, default="System")
    timestamp = Column(DateTime, default=datetime.utcnow)
