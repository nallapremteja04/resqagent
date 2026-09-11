from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database.db import get_db
from backend.models.user import User
from backend.models.responder import Responder
from backend.core.dependencies import (
    require_authenticated_user,
    require_dispatcher,
    require_admin
)
from backend.schemas.responder_schema import ResponderCreate, ResponderStatusUpdate, ResponderResponse

router = APIRouter()

@router.post("/", response_model=ResponderResponse, status_code=status.HTTP_201_CREATED)
def create_responder(
    responder_in: ResponderCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to register new responder operational unit."""
    responder = Responder(
        name=responder_in.name,
        role=responder_in.role,
        specialization=responder_in.specialization or "General",
        availability=responder_in.availability or "AVAILABLE",
        distance=responder_in.distance or 1.0,
        phone=responder_in.phone,
        current_location=responder_in.current_location or "Central Station"
    )
    db.add(responder)
    db.commit()
    db.refresh(responder)
    return responder

@router.get("/", response_model=List[ResponderResponse])
def get_responders(
    availability: Optional[str] = None,
    specialization: Optional[str] = None,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """
    Fleet visibility:
    - Dispatchers & Admins: Full fleet roster.
    - Responders: Their own responder profile.
    - Citizens: Access forbidden.
    """
    if current_user.role == "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Citizens cannot view operational responder fleets."
        )

    query = db.query(Responder)

    if current_user.role == "responder":
        resp = db.query(Responder).filter(Responder.user_id == current_user.id).first()
        if resp:
            return [resp]

    if availability:
        query = query.filter(Responder.availability == availability.upper())
    if specialization:
        query = query.filter(Responder.specialization.ilike(f"%{specialization}%"))

    return query.order_by(Responder.distance.asc()).all()

@router.get("/{responder_id}", response_model=ResponderResponse)
def get_responder(
    responder_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Fetches details of a specific responder."""
    if current_user.role == "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden."
        )

    responder = db.query(Responder).filter(Responder.id == responder_id).first()
    if not responder:
        raise HTTPException(status_code=404, detail="Responder not found")

    if current_user.role == "responder" and responder.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view your own profile."
        )

    return responder

@router.patch("/{responder_id}/status", response_model=ResponderResponse)
def update_responder_status(
    responder_id: int,
    status_in: ResponderStatusUpdate,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db)
):
    """Updates responder availability (Responder updating self or Dispatcher/Admin)."""
    responder = db.query(Responder).filter(Responder.id == responder_id).first()
    if not responder:
        raise HTTPException(status_code=404, detail="Responder not found")

    # Only self or dispatcher/admin can update
    if current_user.role == "responder" and responder.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot change another responder's status."
        )
    elif current_user.role not in ["responder", "dispatcher", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    responder.availability = status_in.availability.upper()
    db.commit()
    db.refresh(responder)
    return responder