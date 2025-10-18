from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

# Base schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    first_name: str = Field(..., min_length=1, max_length=80, description="First name")
    last_name: str = Field(..., min_length=1, max_length=80, description="Last name")
    phone: Optional[str] = Field(None, max_length=30, description="Phone number")

# Authentication schemas
class UserSignUp(UserBase):
    password: str = Field(..., min_length=8, max_length=100, description="Password")

class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class PasswordForgot(BaseModel):
    email: EmailStr = Field(..., description="Email address")

class PasswordReset(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")

class PasswordResetConfirm(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")

# Response schemas
class UserResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class MessageResponse(BaseModel):
    message: str
