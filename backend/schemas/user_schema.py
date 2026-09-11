from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "citizen"
    location: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str
    location: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True