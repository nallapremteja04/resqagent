import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "resqagent-super-secret-jwt-key-32-chars-min-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 24 Hours

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt with salt rounds."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
