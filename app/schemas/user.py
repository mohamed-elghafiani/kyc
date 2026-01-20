# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

from app.models.user import UserRole, UserStatus


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: Optional[UserRole] = UserRole.AGENT


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    
    class Config:
        from_attributes = True