from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.models.user import User
from backend.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_token_from_request(request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Retrieves access token from Authorization header or HTTP cookie."""
    if bearer_token:
        return bearer_token
    # Fallback to cookie if present
    cookie_token = request.cookies.get("resqagent_token")
    if cookie_token:
        return cookie_token
    return None

def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates token and returns the active authenticated user.
    Raises 401 Unauthorized if token is missing, invalid, or expired.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated. Contact administrator."
        )

    return user

def require_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    """Guarantees an authenticated and active user."""
    return current_user

def require_role(*allowed_roles: str) -> Callable:
    """
    Factory dependency verifying that the authenticated user
    possesses one of the permitted roles.
    Raises 403 Forbidden if not authorized.
    """
    normalized_allowed = [r.lower() for r in allowed_roles]

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = (current_user.role or "").lower()
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles [{', '.join(allowed_roles)}]"
            )
        return current_user

    return role_checker

# Role-specific dependency shortcuts
require_citizen = require_role("citizen", "admin")
require_responder = require_role("responder", "admin")
require_dispatcher = require_role("dispatcher", "admin")
require_admin = require_role("admin")
