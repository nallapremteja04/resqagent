"""
Verification script testing the complete Agentic Cognitive Loop:
Scenario:
1. Reset database with demo responders
2. Create incident: "Major car crash on highway, smoke rising, passenger trapped and bleeding"
3. Run orchestrator -> Verifies AnalysisAgent & SelectionAgent assign Suresh (0.8km)
4. Simulate timeout on Suresh -> Verifies EscalationAgent adapts and re-assigns Ravi (1.5km)
5. Ravi accepts & completes -> Verifies AI Incident Report Agent synthesizes postmortem
"""
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.db import SessionLocal
from backend.database.seed_data import seed_database
from backend.models.incident import Incident
from backend.models.assignment import Assignment
from backend.models.responder import Responder
from backend.models.agent_action import AgentAction
from backend.models.report import Report
from backend.agents.orchestrator import AgentOrchestrator

def run_test():
    print("=== STARTING RESQAGENT VERIFICATION ===")
    db = SessionLocal()
    try:
        # Step 0: Seed fresh baseline
        seed_database(db, force=True)
        responders = db.query(Responder).all()
        print(f"[OK] Seeded {len(responders)} responders: {[r.name for r in responders]}")

        # Step 1: Create new emergency incident
        incident = Incident(
            reporter_name="Rahul Sharma",
            emergency_type="Accident",
            description="Major car crash on highway, smoke rising, passenger trapped and bleeding heavily",
            location="Highway 101, Mile Marker 42",
            status="NEW"
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        print(f"[OK] Created Incident #{incident.id}: '{incident.description}'")

        # Step 2: Run Orchestrator Pipeline (PERCEIVE -> REASON -> DECIDE -> ACT)
        AgentOrchestrator.process_new_incident(incident.id, db=db)
        db.refresh(incident)
        print(f"[OK] Triage Completed: Type={incident.emergency_type}, Severity={incident.severity}, Priority={incident.priority}")
        print(f"[OK] Incident Status: {incident.status}")

        first_assignment = db.query(Assignment).filter(Assignment.incident_id == incident.id).first()
        first_resp = db.query(Responder).filter(Responder.id == first_assignment.responder_id).first()
        print(f"[OK] Primary Assigned Unit: {first_resp.name} ({first_resp.role}, {first_resp.distance} km away)")
        assert first_resp.name == "Suresh", f"Expected Suresh, got {first_resp.name}"

        # Step 3: Simulate Timeout / No Response from Suresh
        print("\n--- SIMULATING TIMEOUT ON PRIMARY RESPONDER (SURESH) ---")
        first_assignment.assignment_status = "TIMEOUT"
        first_resp.availability = "AVAILABLE"
        first_resp.active_incident_id = None
        incident.status = "NO_RESPONSE"
        db.commit()

        # Step 4: Run Adaptive Escalation (OBSERVE -> ADAPT)
        escalation_result = AgentOrchestrator.handle_escalation(incident.id, reason="SLA Timeout Expired", db=db)
        db.refresh(incident)
        print(f"[OK] Escalation Result: {escalation_result}")
        assert escalation_result["status"] == "REASSIGNED"
        assert escalation_result["new_responder"] == "Ravi", f"Expected Ravi, got {escalation_result['new_responder']}"

        # Step 5: Ravi Accepts and Completes Assistance
        latest_assignment = (
            db.query(Assignment)
            .filter(Assignment.incident_id == incident.id)
            .order_by(Assignment.assigned_at.desc())
            .first()
        )
        latest_assignment.assignment_status = "ACCEPTED"
        db.commit()
        print(f"[OK] Ravi accepted assignment #{latest_assignment.id}")

        # Mark completed
        latest_assignment.assignment_status = "COMPLETED"
        incident.status = "RESOLVED"
        db.commit()
        print("[OK] Assistance marked COMPLETED, status transitioned to RESOLVED")

        # Step 6: Generate Final Incident Report
        report = AgentOrchestrator.generate_report(incident.id, db=db)
        print(f"\n[OK] AI Incident Report Generated! Report ID #{report.id}")
        print(f"Summary: {report.summary}")
        print(f"Initial: {report.initial_responder} -> Escalated To: {report.final_responder}")
        print(f"Escalation Count: {report.escalation_count}")

        # Verify AgentActions trace
        actions = db.query(AgentAction).filter(AgentAction.incident_id == incident.id).all()
        print(f"\n[OK] Recorded {len(actions)} Agent Actions in Cognitive Trace:")
        for a in actions:
            print(f"  - [{a.agent_name}] {a.action_type}: {a.reasoning}")

        print("\n=== ALL VERIFICATION CHECKS PASSED PERFECTLY ===")

    finally:
        db.close()

if __name__ == "__main__":
    run_test()
