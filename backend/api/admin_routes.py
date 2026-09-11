from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.user import User
from backend.models.responder import Responder
from backend.models.incident import Incident
from backend.models.agent_action import AgentAction
from backend.core.dependencies import require_admin
from backend.core.security import hash_password
from backend.schemas.auth_schema import (
    SafeUser,
    AdminUserCreate,
    AdminUserStatusUpdate
)
from backend.schemas.responder_schema import ResponderCreate, ResponderResponse

router = APIRouter()

@router.get("/users", response_model=List[SafeUser])
def get_all_users(
    role: Optional[str] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to view all system user accounts."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.lower())
    users = query.order_by(User.created_at.desc()).all()
    
    results = []
    for u in users:
        resp_id = None
        if u.role == "responder":
            resp = db.query(Responder).filter(Responder.user_id == u.id).first()
            if resp:
                resp_id = resp.id
        results.append(SafeUser(
            id=u.id,
            name=u.name,
            email=u.email,
            phone=u.phone,
            role=u.role,
            is_active=u.is_active,
            location=u.location,
            created_at=u.created_at,
            last_login=u.last_login,
            responder_id=resp_id
        ))
    return results

@router.post("/users", response_model=SafeUser, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    user_in: AdminUserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-controlled creation of Dispatchers, Responders, or Administrators.
    Public registration is restricted to citizens only.
    """
    email_clean = user_in.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    role_clean = user_in.role.strip().lower()
    if role_clean not in ["citizen", "responder", "dispatcher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: citizen, responder, dispatcher, admin"
        )

    new_user = User(
        name=user_in.name.strip(),
        email=email_clean,
        phone=user_in.phone.strip() if user_in.phone else None,
        password_hash=hash_password(user_in.password),
        role=role_clean,
        location=user_in.location or "Central Station",
        is_active=True,
        last_login=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If role is responder, also link/create the Responder profile
    responder_id = None
    if role_clean == "responder":
        resp = Responder(
            user_id=new_user.id,
            name=new_user.name,
            role=user_in.responder_role or "First Responder",
            specialization=user_in.specialization or "Medical",
            availability="AVAILABLE",
            distance=user_in.distance or 1.0,
            phone=new_user.phone,
            current_location=new_user.location or "Central Station"
        )
        db.add(resp)
        db.commit()
        db.refresh(resp)
        responder_id = resp.id

    return SafeUser(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        phone=new_user.phone,
        role=new_user.role,
        is_active=new_user.is_active,
        location=new_user.location,
        created_at=new_user.created_at,
        last_login=new_user.last_login,
        responder_id=responder_id
    )

@router.patch("/users/{user_id}/status", response_model=SafeUser)
def toggle_user_status(
    user_id: int,
    status_in: AdminUserStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to activate or deactivate a user account."""
    if user_id == current_admin.id and not status_in.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own administrator account."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = status_in.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return SafeUser(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        location=user.location,
        created_at=user.created_at,
        last_login=user.last_login
    )

@router.get("/system-stats")
def get_system_audit_stats(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Audit statistics for administrative overview."""
    return {
        "total_users": db.query(User).count(),
        "total_responders": db.query(Responder).count(),
        "total_incidents": db.query(Incident).count(),
        "total_agent_actions": db.query(AgentAction).count(),
        "system_status": "ONLINE"
    }
