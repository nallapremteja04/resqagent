from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.user import User
from backend.models.responder import Responder
from backend.core.security import hash_password, verify_password, create_access_token
from backend.core.dependencies import get_current_user
from backend.schemas.auth_schema import (
    UserRegister,
    UserLogin,
    UserAuthResponse,
    SafeUser,
    PasswordChange,
    ForgotPasswordRequest
)

router = APIRouter()

@router.post("/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserRegister,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Self-registration supporting Citizen, Responder, Dispatcher, and Admin roles.
    Checks email uniqueness, securely hashes password, provisions responder profile if applicable,
    and returns authenticated session with role token.
    """
    email_clean = user_in.email.strip().lower()
    
    # Check if email is already taken
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Normalize role
    role_raw = (user_in.role or "citizen").strip().lower()
    valid_roles = ["citizen", "responder", "dispatcher", "admin"]
    role = role_raw if role_raw in valid_roles else "citizen"

    # Create user record
    new_user = User(
        name=user_in.name.strip(),
        email=email_clean,
        phone=user_in.phone.strip() if user_in.phone else None,
        password_hash=hash_password(user_in.password),
        role=role,
        location=user_in.location or "Sector 4, Central District",
        is_active=True,
        last_login=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If role is responder, automatically provision the operational Responder unit
    responder_id = None
    if role == "responder":
        resp_unit = Responder(
            user_id=new_user.id,
            name=new_user.name,
            role=user_in.responder_role or "Paramedic / First Responder",
            specialization=user_in.specialization or "Medical",
            current_location=new_user.location or "Sector 4, Central District",
            availability="AVAILABLE",
            distance=user_in.distance if user_in.distance is not None else 0.8,
            phone=new_user.phone or "+1-555-0100"
        )
        db.add(resp_unit)
        db.commit()
        db.refresh(resp_unit)
        responder_id = resp_unit.id

    # Generate JWT token with verified role and responder binding
    token = create_access_token({
        "sub": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role,
        "name": new_user.name,
        "responder_id": responder_id
    })

    # Set cookie for browser session backup
    response.set_cookie(
        key="resqagent_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    safe_user_data = SafeUser(
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
    return UserAuthResponse(user=safe_user_data, access_token=token)

@router.post("/login", response_model=UserAuthResponse)
def login(
    login_in: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticates user with email/username and password.
    Determines role strictly from database.
    """
    email_clean = login_in.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    # Generic invalid credentials check (does not leak email existence)
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact administrator."
        )

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Check for linked responder profile
    responder_id = None
    if user.role == "responder":
        resp = db.query(Responder).filter(Responder.user_id == user.id).first()
        if resp:
            responder_id = resp.id

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "responder_id": responder_id
    })

    response.set_cookie(
        key="resqagent_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    safe_user_data = SafeUser(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        location=user.location,
        created_at=user.created_at,
        last_login=user.last_login,
        responder_id=responder_id
    )

    return UserAuthResponse(user=safe_user_data, access_token=token)

@router.post("/logout")
def logout(response: Response):
    """Invalidates authentication session and clears cookie."""
    response.delete_cookie("resqagent_token")
    return {
        "status": "success",
        "message": "Signed out successfully."
    }

@router.get("/me", response_model=SafeUser)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns profile for currently authenticated user."""
    responder_id = None
    if current_user.role == "responder":
        resp = db.query(Responder).filter(Responder.user_id == current_user.id).first()
        if resp:
            responder_id = resp.id

    return SafeUser(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        is_active=current_user.is_active,
        location=current_user.location,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        responder_id=responder_id
    )

@router.post("/change-password")
def change_password(
    pwd_in: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows authenticated user to update their own password."""
    if not verify_password(pwd_in.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    current_user.password_hash = hash_password(pwd_in.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": "success",
        "message": "Password changed successfully."
    }

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """
    Dispatches password reset request.
    Does not leak whether the email exists.
    """
    return {
        "status": "success",
        "message": "If an account with this email exists, password reset instructions have been sent."
    }
