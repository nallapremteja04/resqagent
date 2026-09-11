from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class SafeUser(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    location: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    responder_id: Optional[int] = None

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    confirm_password: str
    location: Optional[str] = None
    role: Optional[str] = "citizen"
    responder_role: Optional[str] = None
    specialization: Optional[str] = None
    distance: Optional[float] = 1.0

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class UserAuthResponse(BaseModel):
    user: SafeUser
    access_token: str
    token_type: str = "bearer"

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("New password must be at least 6 characters long")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New passwords do not match")
        return v

class ForgotPasswordRequest(BaseModel):
    email: str

class AdminUserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str  # citizen, responder, dispatcher, admin
    phone: Optional[str] = None
    location: Optional[str] = None

    # Optional responder parameters if role is responder
    responder_role: Optional[str] = "First Responder"
    specialization: Optional[str] = "Medical"
    distance: Optional[float] = 1.0

class AdminUserStatusUpdate(BaseModel):
    is_active: bool
