from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserSignUp, UserLogin, PasswordForgot, PasswordReset,
    AuthResponse, Token, MessageResponse
)
from app.core.config import settings

router = APIRouter()

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserSignUp,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (8-100 characters)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number
    """
    auth_service = AuthService(db)
    user, access_token = await auth_service.signup(user_data)
    
    return AuthResponse(
        user=user,
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    - **username**: Username or email
    - **password**: User password
    """
    auth_service = AuthService(db)
    user, access_token = await auth_service.login(login_data)
    
    return AuthResponse(
        user=user,
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/password/forgot", response_model=MessageResponse)
async def forgot_password(
    forgot_data: PasswordForgot,
    db: Session = Depends(get_db)
):
    """
    Request password reset token.
    
    - **email**: User's email address
    """
    auth_service = AuthService(db)
    message = await auth_service.forgot_password(forgot_data.email)
    
    return MessageResponse(message=message)

@router.post("/password/reset", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password
    """
    auth_service = AuthService(db)
    await auth_service.reset_password(reset_data.token, reset_data.new_password)
    
    return MessageResponse(message="Password has been reset successfully")

@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user (invalidate all sessions).
    """
    auth_service = AuthService(db)
    await auth_service.logout(current_user.user_id)
    
    return MessageResponse(message="Logged out successfully")
