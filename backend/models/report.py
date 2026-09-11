from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from datetime import datetime
from backend.database.db import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    
    summary = Column(Text, nullable=False)
    emergency_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    
    initial_responder = Column(String, nullable=True)
    final_responder = Column(String, nullable=True)
    escalation_count = Column(Integer, default=0)
    response_time_seconds = Column(Float, default=0.0)
    final_status = Column(String, default="RESOLVED")
    
    full_report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
