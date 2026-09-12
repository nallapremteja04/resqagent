from sqlalchemy.orm import Session
from backend.models.responder import Responder
from backend.models.user import User
from backend.models.incident import Incident
from backend.models.assignment import Assignment
from backend.models.notification import Notification
from backend.models.incident_timeline import IncidentTimeline
from backend.models.agent_action import AgentAction
from backend.models.report import Report
from backend.core.security import hash_password

def seed_database(db: Session, force: bool = False):
    """
    Test fixtures seeding baseline responders and demo test users:
    - Suresh: 0.8 km, Available (Medical / First Responder)
    - Ravi: 1.5 km, Available (Senior Trauma Doctor)
    - Priya: 0.5 km, Busy (Critical Care Nurse)
    - Kumar: 3.2 km, Available (Fire & Rescue Specialist)
    - Anita: 4.5 km, Available (Emergency Police Patrol)
    """
    if force:
        db.query(Report).delete()
        db.query(AgentAction).delete()
        db.query(IncidentTimeline).delete()
        db.query(Notification).delete()
        db.query(Assignment).delete()
        db.query(Incident).delete()
        db.query(Responder).delete()
        # Preserve administrators during fixture cleanup
        db.query(User).filter(User.role != "admin").delete()
        db.commit()

    # Ensure admin user is never missing
    if db.query(User).filter(User.role == "admin").count() == 0:
        admin_user = User(
            name="System Administrator",
            email="admin@resqagent.org",
            password_hash=hash_password("ResQAdmin2026!"),
            role="admin",
            location="Emergency Operations Command",
            is_active=True
        )
        db.add(admin_user)
        db.commit()

    default_hash = hash_password("DemoPassword123!")

    if db.query(Responder).count() == 0:
        responders = [
            Responder(
                name="Suresh",
                role="Paramedic / First Responder",
                specialization="Medical",
                availability="AVAILABLE",
                distance=0.8,
                phone="+1-555-0101",
                current_location="Sector 3 Rapid Post"
            ),
            Responder(
                name="Ravi",
                role="Senior Trauma Specialist",
                specialization="Medical",
                availability="AVAILABLE",
                distance=1.5,
                phone="+1-555-0102",
                current_location="Central Hospital Base"
            ),
            Responder(
                name="Priya",
                role="Critical Care Nurse",
                specialization="Medical",
                availability="BUSY",
                distance=0.5,
                phone="+1-555-0103",
                current_location="Downtown Clinic"
            ),
            Responder(
                name="Kumar",
                role="Fire & Heavy Rescue Specialist",
                specialization="Rescue",
                availability="AVAILABLE",
                distance=3.2,
                phone="+1-555-0104",
                current_location="Station 7 Firehouse"
            ),
            Responder(
                name="Anita",
                role="Emergency Police Patrol",
                specialization="Police",
                availability="AVAILABLE",
                distance=4.5,
                phone="+1-555-0105",
                current_location="West Precinct Patrol"
            )
        ]
        db.add_all(responders)
        db.commit()

    if db.query(User).count() == 0:
        users = [
            User(
                name="Rahul Sharma",
                phone="+1-555-7788",
                email="rahul@example.com",
                password_hash=default_hash,
                role="citizen",
                location="Highway 101, Mile Marker 42",
                is_active=True
            ),
            User(
                name="Dispatch Coordinator",
                phone="+1-555-9999",
                email="dispatch@resqagent.org",
                password_hash=default_hash,
                role="dispatcher",
                location="City Emergency Operations Center",
                is_active=True
            )
        ]
        db.add_all(users)
        db.commit()
