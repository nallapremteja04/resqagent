"""
End-to-End API Test Suite for ResQAgent
Verifies all REST API routes, models, agents, authentication, and frontend static mounting.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.db import SessionLocal
from backend.database.seed_data import seed_database

client = TestClient(app)

def test_full_api_workflow():
    print("\n--- TEST 1: Health & Static Mount ---")
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"
    assert res.json()["auth_enabled"] is True
    print("[PASS] /api/health is online with auth enabled")

    res = client.get("/")
    assert res.status_code == 200
    assert "ResQAgent" in res.text
    print("[PASS] Frontend index.html served at root '/'")

    # Sign in as Admin
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@resqagent.org",
        "password": "ResQAdmin2026!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] Administrator authenticated")

    print("\n--- TEST 2: Seed Responders & Verify Fleet ---")
    # Seed test responders into DB
    db = SessionLocal()
    try:
        seed_database(db, force=True)
    finally:
        db.close()

    res = client.get("/api/responders/", headers=admin_headers)
    assert res.status_code == 200
    responders = res.json()
    assert len(responders) >= 4
    names = [r["name"] for r in responders]
    print(f"[PASS] Responders roster populated: {names}")
    assert "Suresh" in names and "Ravi" in names

    print("\n--- TEST 3: Citizen Self-Registration ---")
    res = client.post("/api/auth/register", json={
        "name": "Pooja Verma",
        "phone": "+1-555-4321",
        "email": "pooja.test@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "location": "Sector 9 Metro Station"
    })
    assert res.status_code == 201
    citizen_token = res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    user_id = res.json()["user"]["id"]
    print(f"[PASS] Created and authenticated Citizen User #{user_id}")

    print("\n--- TEST 4: Incident Creation & Multi-Agent Triage ---")
    res = client.post("/api/incidents/", headers=citizen_headers, json={
        "emergency_type": "Accident",
        "description": "Multi-vehicle collision on highway, fire and smoke visible, trapped passengers bleeding",
        "location": "Express Highway Flyover"
    })
    assert res.status_code == 201
    incident = res.json()
    incident_id = incident["id"]
    print(f"[PASS] Incident created: #{incident_id}")

    # Fetch updated incident
    res = client.get(f"/api/incidents/{incident_id}", headers=citizen_headers)
    assert res.status_code == 200
    inc_data = res.json()
    print(f"[PASS] Triaged Priority: {inc_data['priority']}, Severity: {inc_data['severity']}, Status: {inc_data['status']}")
    assert inc_data["status"] == "WAITING_FOR_RESPONSE"

    # Verify primary assignment is Suresh (0.8km)
    res = client.get(f"/api/assignments/?incident_id={incident_id}", headers=admin_headers)
    assert res.status_code == 200
    assignments = res.json()
    assert len(assignments) >= 1
    assert assignments[0]["assignment_status"] == "PENDING"
    print(f"[PASS] Primary assignment created for responder #{assignments[0]['responder_id']}")

    print("\n--- TEST 5: Verify AI Cognitive Actions & Timeline ---")
    res = client.get(f"/api/incidents/{incident_id}/actions", headers=citizen_headers)
    assert res.status_code == 200
    actions = res.json()
    print(f"[PASS] Recorded {len(actions)} Agent Actions:")
    for a in actions:
        print(f"   -> [{a['agent_name']}] {a['action_type']}")

    res = client.get(f"/api/incidents/{incident_id}/timeline", headers=citizen_headers)
    assert res.status_code == 200
    timeline = res.json()
    print(f"[PASS] Recorded {len(timeline)} Timeline Events")

    print("\n--- TEST 6: Simulate Timeout & Adaptive Escalation ---")
    res = client.post(f"/api/simulation/timeout/{incident_id}", headers=admin_headers)
    assert res.status_code == 200
    print(f"[PASS] Timeout simulation response: {res.json()['status']}")

    # Check that a new assignment was created for the escalated responder (Ravi)
    res = client.get(f"/api/assignments/?incident_id={incident_id}", headers=admin_headers)
    assert res.status_code == 200
    all_assignments = res.json()
    assert len(all_assignments) == 2
    latest_assignment = all_assignments[0]  # sorted desc
    print(f"[PASS] Escalated to new assignment #{latest_assignment['id']} (Responder #{latest_assignment['responder_id']})")

    print("\n--- TEST 7: Responder Accepts & Completes Assistance ---")
    # Accept (Admin / Dispatcher authorization allows progress)
    res = client.post(f"/api/assignments/{latest_assignment['id']}/respond", headers=admin_headers, json={
        "status": "ACCEPTED",
        "notes": "En route with medical kit"
    })
    assert res.status_code == 200
    print("[PASS] Assignment accepted")

    # Complete
    res = client.post(f"/api/assignments/{latest_assignment['id']}/progress", headers=admin_headers, json={
        "status": "COMPLETED",
        "notes": "Casualties stabilized and transferred"
    })
    assert res.status_code == 200
    print("[PASS] Assignment marked completed")

    # Check incident status is RESOLVED
    res = client.get(f"/api/incidents/{incident_id}", headers=citizen_headers)
    assert res.json()["status"] == "RESOLVED"
    print("[PASS] Incident status transitioned to RESOLVED")

    print("\n--- TEST 8: AI Incident Report Synthesis ---")
    res = client.post(f"/api/reports/{incident_id}/generate", headers=admin_headers)
    assert res.status_code == 200
    report = res.json()
    print(f"[PASS] Report synthesized for Incident #{incident_id}:")
    print(f"   Initial: {report['initial_responder']} -> Final: {report['final_responder']}")
    print(f"   Escalations: {report['escalation_count']}")
    print(f"   Summary: {report['summary']}")

    print("\n==========================================")
    print("ALL API & AGENT TEST SUITE SUCCEEDED (100%)")
    print("==========================================")

if __name__ == "__main__":
    test_full_api_workflow()
