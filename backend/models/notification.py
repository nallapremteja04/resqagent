from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from backend.database.db import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    
    # Recipient: RESPONDER, USER, GUARDIAN, DISPATCH, HOSPITAL, POLICE
    recipient_type = Column(String, nullable=False)
    recipient_name = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String, default="IN_APP")
    status = Column(String, default="SENT")  # SENT, DELIVERED, READ
    sent_at = Column(DateTime, default=datetime.utcnow)
