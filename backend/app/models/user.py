from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(30))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    auth_sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    catalogue_items = relationship("CatalogueItem", back_populates="seller")
    auctions = relationship("Auction", back_populates="winning_bidder")
    bids = relationship("Bid", back_populates="bidder")
    orders = relationship("Order", back_populates="buyer")


class Address(Base):
    __tablename__ = "addresses"

    address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    street_line1 = Column(String(200), nullable=False)
    street_line2 = Column(String(200))
    city = Column(String(120), nullable=False)
    state_region = Column(String(120))
    postal_code = Column(String(30), nullable=False)
    country = Column(String(120), nullable=False)
    is_default_shipping = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="shipping_address")

    # Indexes
    __table_args__ = (
        Index('idx_addresses_user', 'user_id'),
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    user_agent = Column(Text)
    ip_address = Column(String(45))  # IPv6 can be up to 45 chars
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", back_populates="auth_sessions")

    # Indexes
    __table_args__ = (
        Index('idx_auth_sessions_user', 'user_id'),
        Index('idx_auth_sessions_expires', 'expires_at'),
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")

    # Indexes
    __table_args__ = (
        Index('idx_pwd_reset_user', 'user_id'),
    )
