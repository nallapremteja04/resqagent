"""
Comprehensive Authentication & RBAC Security Test Suite for ResQAgent
Tests all 17 required scenarios:
1. Citizen registration
2. Citizen login
3. Invalid login handling
4. Responder login
5. Dispatcher login
6. Admin login
7. Authenticated /me
8. Logout
9. Expired/invalid session/token
10. Unauthorized API access
11. Citizen attempting dispatcher endpoint (403)
12. Responder attempting admin endpoint (403)
13. Dispatcher attempting admin endpoint (403)
14. Admin access
15. Password hashing verification
16. Password change
17. Citizen incident ownership & privacy isolation
"""
import sys
import os
from datetime import timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.db import SessionLocal
from backend.models.user import User
from backend.core.security import create_access_token

client = TestClient(app)

def run_auth_test_suite():
    print("==================================================")
    print("STARTING RESQAGENT AUTHENTICATION & RBAC TEST SUITE")
    print("==================================================")

    # Clean up test user artifacts if previously run
    db = SessionLocal()
    try:
        db.query(User).filter(User.email.in_([
            "jane@example.com", "bob@example.com", "other_citizen@example.com", 
            "suresh@resqagent.org", "dispatch@resqagent.org", "dispatcher@resqagent.org",
            "officer_ravi@resqagent.org", "dispatcher_dan@resqagent.org"
        ])).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    # 1. Citizen Registration
    print("\n--- 1. Citizen Registration ---")
    reg_res = client.post("/api/auth/register", json={
        "name": "Jane Citizen",
        "email": "jane@example.com",
        "phone": "+1-555-1122",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "location": "Downtown Metro"
    })
    assert reg_res.status_code == 201, f"Failed: {reg_res.text}"
    citizen_token = reg_res.json()["access_token"]
    citizen_user = reg_res.json()["user"]
    assert citizen_user["role"] == "citizen"
    assert "password" not in citizen_user and "password_hash" not in citizen_user
    print("[PASS] Citizen self-registered with token.")

    # Duplicate registration check
    dup_res = client.post("/api/auth/register", json={
        "name": "Jane Duplicate",
        "email": "jane@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert dup_res.status_code == 400
    print("[PASS] Duplicate email registration rejected.")

    # 2. Citizen Login
    print("\n--- 2. Citizen Login ---")
    login_res = client.post("/api/auth/login", json={
        "email": "jane@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    assert login_res.json()["user"]["email"] == "jane@example.com"
    print("[PASS] Citizen login successful.")

    # 3. Invalid Login Handling
    print("\n--- 3. Invalid Login Handling ---")
    # Wrong password
    wrong_pwd = client.post("/api/auth/login", json={
        "email": "jane@example.com",
        "password": "WrongPassword!"
    })
    assert wrong_pwd.status_code == 401
    assert "Invalid email or password" in wrong_pwd.json()["detail"]

    # Non-existent email
    non_existent = client.post("/api/auth/login", json={
        "email": "ghost@example.com",
        "password": "Password123!"
    })
    assert non_existent.status_code == 401
    print("[PASS] Invalid credentials securely rejected with 401.")

    # 6. Admin Login (Bootstrapped initial admin)
    print("\n--- 6. Admin Login ---")
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@resqagent.org",
        "password": "ResQAdmin2026!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    assert admin_login.json()["user"]["role"] == "admin"
    print("[PASS] Admin login successful.")

    # 4. Responder Creation & Login (Admin controlled)
    print("\n--- 4. Responder Creation & Login ---")
    resp_create = client.post("/api/admin/users", headers=admin_headers, json={
        "name": "Suresh Paramedic",
        "email": "suresh@resqagent.org",
        "password": "ResponderPass1!",
        "role": "responder",
        "phone": "+1-555-0101",
        "responder_role": "Paramedic / First Responder",
        "specialization": "Medical",
        "distance": 0.8
    })
    assert resp_create.status_code == 201
    assert resp_create.json()["role"] == "responder"
    assert resp_create.json()["responder_id"] is not None

    # Sign in as responder
    resp_login = client.post("/api/auth/login", json={
        "email": "suresh@resqagent.org",
        "password": "ResponderPass1!"
    })
    assert resp_login.status_code == 200
    responder_token = resp_login.json()["access_token"]
    responder_headers = {"Authorization": f"Bearer {responder_token}"}
    assert resp_login.json()["user"]["role"] == "responder"
    print("[PASS] Responder created by admin and authenticated successfully.")

    # 5. Dispatcher Creation & Login (Admin controlled)
    print("\n--- 5. Dispatcher Creation & Login ---")
    disp_create = client.post("/api/admin/users", headers=admin_headers, json={
        "name": "Operations Dispatcher",
        "email": "dispatch@resqagent.org",
        "password": "DispatcherPass1!",
        "role": "dispatcher",
        "phone": "+1-555-0999"
    })
    assert disp_create.status_code == 201
    assert disp_create.json()["role"] == "dispatcher"

    disp_login = client.post("/api/auth/login", json={
        "email": "dispatch@resqagent.org",
        "password": "DispatcherPass1!"
    })
    assert disp_login.status_code == 200
    dispatcher_token = disp_login.json()["access_token"]
    dispatcher_headers = {"Authorization": f"Bearer {dispatcher_token}"}
    print("[PASS] Dispatcher created by admin and authenticated successfully.")

    # 7. Authenticated /me
    print("\n--- 7. Authenticated /api/auth/me ---")
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {citizen_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "jane@example.com"
    assert me_res.json()["role"] == "citizen"
    print("[PASS] /api/auth/me returned correct authenticated profile.")

    # 8. Logout
    print("\n--- 8. Logout ---")
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200
    print("[PASS] Logout acknowledged.")

    # 9. Expired / Invalid Token
    print("\n--- 9. Expired / Invalid Token ---")
    # Tampered token
    invalid_res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.signature"})
    assert invalid_res.status_code == 401

    # Expired token
    expired_token = create_access_token({"sub": str(citizen_user["id"])}, expires_delta=timedelta(seconds=-10))
    expired_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired_res.status_code == 401
    print("[PASS] Invalid and expired tokens rejected with 401.")

    # 10. Unauthorized API Access without token
    print("\n--- 10. Unauthorized Access Without Token ---")
    no_auth = client.get("/api/incidents/")
    assert no_auth.status_code == 401
    print("[PASS] Protected incident endpoint rejected unauthenticated request.")

    # 11. Citizen attempting dispatcher endpoint (403 Forbidden)
    print("\n--- 11. Citizen Attempting Dispatcher Endpoint ---")
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    c_forbidden = client.get("/api/reports/", headers=citizen_headers)
    assert c_forbidden.status_code == 403
    print(f"[PASS] Citizen blocked from dispatcher reports (403 Forbidden).")

    # 12. Responder attempting admin endpoint (403 Forbidden)
    print("\n--- 12. Responder Attempting Admin Endpoint ---")
    r_forbidden = client.get("/api/admin/users", headers=responder_headers)
    assert r_forbidden.status_code == 403
    print("[PASS] Responder blocked from admin user management (403 Forbidden).")

    # 13. Dispatcher attempting admin endpoint (403 Forbidden)
    print("\n--- 13. Dispatcher Attempting Admin Endpoint ---")
    d_forbidden = client.get("/api/admin/users", headers=dispatcher_headers)
    assert d_forbidden.status_code == 403
    print("[PASS] Dispatcher blocked from admin user management (403 Forbidden).")

    # 14. Admin Access to Admin Endpoints (200 OK)
    print("\n--- 14. Admin Access to Admin Endpoints ---")
    admin_users = client.get("/api/admin/users", headers=admin_headers)
    assert admin_users.status_code == 200
    assert len(admin_users.json()) >= 4
    print(f"[PASS] Admin successfully retrieved system users list ({len(admin_users.json())} users).")

    # 15. Password Hashing Verification
    print("\n--- 15. Password Hashing Verification ---")
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.email == "jane@example.com").first()
        assert db_user.password_hash.startswith("$2b$")
        assert "Password123!" not in db_user.password_hash
        print("[PASS] Password verified as securely salted bcrypt hash; no plain text stored.")
    finally:
        db.close()

    # 16. Password Change Functionality
    print("\n--- 16. Password Change Functionality ---")
    change_res = client.post("/api/auth/change-password", headers=citizen_headers, json={
        "current_password": "Password123!",
        "new_password": "BrandNewPassword2026!",
        "confirm_password": "BrandNewPassword2026!"
    })
    assert change_res.status_code == 200

    # Verify old password no longer works
    old_login = client.post("/api/auth/login", json={
        "email": "jane@example.com",
        "password": "Password123!"
    })
    assert old_login.status_code == 401

    # Verify new password works
    new_login = client.post("/api/auth/login", json={
        "email": "jane@example.com",
        "password": "BrandNewPassword2026!"
    })
    assert new_login.status_code == 200
    citizen_headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}
    print("[PASS] Password change verified: old password invalidated, new password active.")

    # 17. Citizen Incident Privacy & Ownership Isolation
    print("\n--- 17. Citizen Incident Privacy & Ownership Isolation ---")
    # Register Citizen B
    cit_b = client.post("/api/auth/register", json={
        "name": "Citizen Bob",
        "email": "bob@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }).json()
    bob_headers = {"Authorization": f"Bearer {cit_b['access_token']}"}

    # Jane creates incident
    jane_inc = client.post("/api/incidents/", headers=citizen_headers, json={
        "emergency_type": "Medical",
        "description": "Jane's private medical distress call",
        "location": "North District"
    }).json()

    # Bob creates incident
    bob_inc = client.post("/api/incidents/", headers=bob_headers, json={
        "emergency_type": "Fire",
        "description": "Bob's private fire alarm distress call",
        "location": "South District"
    }).json()

    # Jane fetches incidents list -> Must ONLY contain Jane's incident!
    jane_list = client.get("/api/incidents/", headers=citizen_headers).json()
    jane_inc_ids = [i["id"] for i in jane_list]
    assert jane_inc["id"] in jane_inc_ids
    assert bob_inc["id"] not in jane_inc_ids
    print(f"[PASS] Jane's incidents list only contains her own reports.")

    # Bob attempts to view Jane's incident by ID -> Must return 403 Forbidden!
    snoop_res = client.get(f"/api/incidents/{jane_inc['id']}", headers=bob_headers)
    assert snoop_res.status_code == 403
    print(f"[PASS] Cross-citizen data snooping prevented with 403 Forbidden.")

    # Dispatcher fetches incidents list -> Sees BOTH incidents
    disp_list = client.get("/api/incidents/", headers=dispatcher_headers).json()
    disp_inc_ids = [i["id"] for i in disp_list]
    assert jane_inc["id"] in disp_inc_ids and bob_inc["id"] in disp_inc_ids
    print(f"[PASS] Dispatcher has full operational visibility across all incidents.")

    print("\n==================================================")
    print("ALL 17 AUTH & RBAC SECURITY TESTS PASSED (100%)")
    print("==================================================")

if __name__ == "__main__":
    run_auth_test_suite()
