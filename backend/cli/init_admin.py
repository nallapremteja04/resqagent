import argparse
import os
import sys
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.database.db import SessionLocal, engine, Base
import backend.models
from backend.models.user import User
from backend.core.security import hash_password

def create_initial_admin(name: str, email: str, password: str, phone: str = None) -> User:
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        email_clean = email.strip().lower()
        existing = db.query(User).filter(User.email == email_clean).first()
        if existing:
            print(f"[!] User with email '{email_clean}' already exists (Role: {existing.role}).")
            if existing.role != "admin":
                existing.role = "admin"
                existing.password_hash = hash_password(password)
                existing.is_active = True
                db.commit()
                print(f"[✓] Existing user updated to Administrator.")
            return existing

        admin = User(
            name=name.strip(),
            email=email_clean,
            phone=phone,
            password_hash=hash_password(password),
            role="admin",
            location="Emergency Operations Command",
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"[✓] Administrator account successfully created: {admin.email} (ID: {admin.id})")
        return admin
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Initialize ResQAgent Administrator Account")
    parser.add_argument("--name", default=os.getenv("INITIAL_ADMIN_NAME", "System Administrator"), help="Admin Full Name")
    parser.add_argument("--email", default=os.getenv("INITIAL_ADMIN_EMAIL", "admin@resqagent.org"), help="Admin Email")
    parser.add_argument("--password", default=os.getenv("INITIAL_ADMIN_PASSWORD", "ResQAdmin2026!"), help="Admin Password")
    parser.add_argument("--phone", default="+1-555-0000", help="Admin Contact Phone")
    
    args = parser.parse_args()
    create_initial_admin(args.name, args.email, args.password, args.phone)

if __name__ == "__main__":
    main()
