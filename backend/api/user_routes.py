from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.db import get_db
from backend.models.user import User
from backend.core.dependencies import require_authenticated_user, require_admin
from backend.schemas.user_schema import UserResponse

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to list user accounts."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.lower())
    return query.order_by(User.created_at.desc()).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Retrieves user profile (Admin or the user themselves)."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view other users' profile information."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user