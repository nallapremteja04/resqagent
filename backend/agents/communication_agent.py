from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.notification import Notification
from backend.models.incident import Incident
from backend.models.responder import Responder

class CommunicationAgent:
    """
    Communication Agent
    Determines stakeholder target groups and composes tailored alerts:
    - Field Responder: Mission parameters, location, patient condition, ETA expectation
    - Citizen / Caller: Reassurance, responder assignment status, arrival advice
    - Central Dispatch / Operations: Incident triage log, assigned unit
    - Medical Facility / Hospital: Incoming casualty warning for high/critical priority
    """

    @classmethod
    def dispatch_initial_alerts(
        cls,
        db: Session,
        incident: Incident,
        responder: Responder
    ) -> List[Notification]:
        notifications = []

        # 1. Alert to Responder
        resp_msg = (
            f"🚨 PRIORITY DISPATCH ({incident.priority}): {incident.emergency_type} at {incident.location}. "
            f"Details: {incident.description}. Please confirm and accept immediately."
        )
        n_resp = Notification(
            incident_id=incident.id,
            recipient_type="RESPONDER",
            recipient_name=responder.name,
            message=resp_msg,
            channel="APP_PUSH"
        )
        notifications.append(n_resp)

        # 2. Alert to Citizen
        citizen_msg = (
            f"ResQAgent Update: Your emergency request has been triaged as {incident.priority}. "
            f"Responder {responder.name} ({responder.distance} km away) has been dispatched to your location."
        )
        n_citizen = Notification(
            incident_id=incident.id,
            recipient_type="USER",
            recipient_name=incident.reporter_name or "Citizen",
            message=citizen_msg,
            channel="SMS"
        )
        notifications.append(n_citizen)

        # 3. Alert to Central Dispatch
        dispatch_msg = (
            f"LOG [{incident.priority}]: Incident #{incident.id} ({incident.emergency_type}) assigned to "
            f"{responder.name} ({responder.role}). Awaiting 30s confirmation."
        )
        n_dispatch = Notification(
            incident_id=incident.id,
            recipient_type="DISPATCH",
            recipient_name="Regional Emergency Dispatch",
            message=dispatch_msg,
            channel="RADIO"
        )
        notifications.append(n_dispatch)

        # 4. If Critical, Alert Regional Trauma Hospital
        if incident.priority in ["P1-Critical", "Critical"]:
            hospital_msg = (
                f"TRAUMA INBOUND ADVISORY: Potential critical casualty incoming from {incident.location}. "
                f"Category: {incident.emergency_type}. Responding unit: {responder.name}."
            )
            n_hosp = Notification(
                incident_id=incident.id,
                recipient_type="HOSPITAL",
                recipient_name="Trauma Center Unit",
                message=hospital_msg,
                channel="SECURE_NET"
            )
            notifications.append(n_hosp)

        db.add_all(notifications)
        db.commit()
        return notifications

    @classmethod
    def dispatch_escalation_alerts(
        cls,
        db: Session,
        incident: Incident,
        new_responder: Responder,
        failed_responder_name: str,
        reason: str
    ) -> List[Notification]:
        notifications = []

        # 1. Alert to New Responder
        resp_msg = (
            f"⚠️ RE-ROUTED URGENT DISPATCH ({incident.priority}): {incident.emergency_type} at {incident.location}. "
            f"Prior unit was unable to respond. Please accept assistance call immediately."
        )
        notifications.append(Notification(
            incident_id=incident.id,
            recipient_type="RESPONDER",
            recipient_name=new_responder.name,
            message=resp_msg,
            channel="APP_PUSH"
        ))

        # 2. Citizen reassurance
        citizen_msg = (
            f"ResQAgent Reassignment: Primary unit {failed_responder_name} was redirected. "
            f"Senior responder {new_responder.name} ({new_responder.distance} km away) is now assigned to you."
        )
        notifications.append(Notification(
            incident_id=incident.id,
            recipient_type="USER",
            recipient_name=incident.reporter_name or "Citizen",
            message=citizen_msg,
            channel="SMS"
        ))

        # 3. Dispatch log
        notifications.append(Notification(
            incident_id=incident.id,
            recipient_type="DISPATCH",
            recipient_name="Regional Emergency Dispatch",
            message=f"ADAPTIVE ESCALATION: Incident #{incident.id} re-routed to {new_responder.name}. Reason: {reason}",
            channel="RADIO"
        ))

        db.add_all(notifications)
        db.commit()
        return notifications
