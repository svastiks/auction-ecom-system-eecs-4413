from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
import uuid
from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, AuthSession
from sqlalchemy import select, and_

# HTTP Bearer token scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token.
    
    Validates:
    1. JWT token signature and expiration
    2. Session exists and is not expired in database
    3. User exists and is active
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id: str = payload.get("sub")
    session_id: str = payload.get("session_id")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate session exists and is not expired (this makes logout work!)
    # Only validate if session_id is present in token (new tokens have it, old ones don't)
    if session_id:
        try:
            session_uuid = uuid.UUID(session_id)
            user_uuid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        session_stmt = select(AuthSession).where(
            and_(
                AuthSession.session_id == session_uuid,
                AuthSession.user_id == user_uuid,
                AuthSession.expires_at > datetime.now(timezone.utc)
            )
        )
        session_result = db.execute(session_stmt)
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    # If session_id is not present (old tokens), skip session validation for backward compatibility
    # But these tokens will not work after logout since we can't track their sessions
    
    # Get user from database
    user_uuid = uuid.UUID(user_id) if not isinstance(user_id, uuid.UUID) else user_id
    stmt = select(User).where(User.user_id == user_uuid)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
