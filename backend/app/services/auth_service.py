from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from app.models.user import User, AuthSession, PasswordResetToken, Address
from app.core.security import verify_password, get_password_hash, create_access_token, generate_password_reset_token
from app.core.config import settings
from app.schemas.auth import UserSignUp, UserLogin
import uuid

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def signup(self, user_data: UserSignUp) -> Tuple[User, str]:
        """Register a new user."""
        # Check if username already exists
        stmt = select(User).where(User.username == user_data.username)
        existing_user = self.db.execute(stmt).scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email already exists
        stmt = select(User).where(User.email == user_data.email)
        existing_user = self.db.execute(stmt).scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            password_hash=hashed_password,
            is_active=True
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Create address if provided
        if user_data.address:
            address = Address(
                user_id=user.user_id,
                street_line1=user_data.address.street_line1,
                street_line2=user_data.address.street_line2,
                city=user_data.address.city,
                state_region=user_data.address.state_region,
                postal_code=user_data.address.postal_code,
                country=user_data.address.country,
                phone=user_data.address.phone if hasattr(user_data.address, 'phone') and user_data.address.phone else user_data.phone,
                is_default_shipping=user_data.address.is_default_shipping if hasattr(user_data.address, 'is_default_shipping') else True
            )
            self.db.add(address)
            self.db.commit()

        # Create auth session first (to get session_id)
        session = AuthSession(
            user_id=user.user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Create access token with session_id included
        access_token = create_access_token(
            data={
                "sub": str(user.user_id),
                "session_id": str(session.session_id)
            }
        )

        return user, access_token

    async def login(self, login_data: UserLogin) -> Tuple[User, str]:
        """Authenticate user and return access token."""
        # Find user by username or email
        stmt = select(User).where(
            (User.username == login_data.username) | (User.email == login_data.username)
        )
        user = self.db.execute(stmt).scalar_one_or_none()
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create auth session first (to get session_id)
        session = AuthSession(
            user_id=user.user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Create access token with session_id included
        access_token = create_access_token(
            data={
                "sub": str(user.user_id),
                "session_id": str(session.session_id)
            }
        )

        return user, access_token

    async def forgot_password(self, email: str) -> str:
        """Generate password reset token for user."""
        # Find user by email
        stmt = select(User).where(User.email == email)
        user = self.db.execute(stmt).scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists or not for security
            return "If the email exists, a password reset link has been sent."

        # Generate reset token
        reset_token = generate_password_reset_token()
        token_hash = get_password_hash(reset_token)
        
        # Create password reset token
        reset_token_record = PasswordResetToken(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiration
        )
        
        self.db.add(reset_token_record)
        self.db.commit()

        # In a real application, you would send an email here
        # For now, we'll return the token for testing
        return f"Password reset token: {reset_token}"

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password using reset token."""
        # Find valid reset token
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
                PasswordResetToken.used_at.is_(None)
            )
        )
        reset_tokens = self.db.execute(stmt).scalars().all()
        
        # Check if any token matches
        for reset_token_record in reset_tokens:
            if verify_password(token, reset_token_record.token_hash):
                # Get user
                user_stmt = select(User).where(User.user_id == reset_token_record.user_id)
                user = self.db.execute(user_stmt).scalar_one_or_none()
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid reset token"
                    )

                # Update password
                user.password_hash = get_password_hash(new_password)
                
                # Mark token as used
                reset_token_record.used_at = datetime.now(timezone.utc)
                
                # Invalidate all user sessions
                session_stmt = select(AuthSession).where(AuthSession.user_id == user.user_id)
                sessions = self.db.execute(session_stmt).scalars().all()
                for session in sessions:
                    session.expires_at = datetime.now(timezone.utc)  # Expire immediately
                
                self.db.commit()
                return True

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    async def logout(self, user_id: uuid.UUID) -> bool:
        """Logout user by expiring all sessions."""
        stmt = select(AuthSession).where(AuthSession.user_id == user_id)
        sessions = self.db.execute(stmt).scalars().all()
        
        for session in sessions:
            session.expires_at = datetime.now(timezone.utc)  # Expire immediately
        
        self.db.commit()
        return True
