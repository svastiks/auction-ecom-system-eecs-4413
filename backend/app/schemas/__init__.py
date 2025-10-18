# Import all schemas to ensure they are registered
from .auth import (
    UserSignUp, UserLogin, Token, PasswordForgot, PasswordReset, 
    PasswordResetConfirm, UserResponse as AuthUserResponse, AuthResponse, MessageResponse
)
from .user import UserUpdate, UserResponse
from .address import AddressCreate, AddressUpdate, AddressResponse, AddressListResponse

__all__ = [
    # Auth schemas
    "UserSignUp",
    "UserLogin", 
    "Token",
    "PasswordForgot",
    "PasswordReset",
    "PasswordResetConfirm",
    "AuthUserResponse",
    "AuthResponse",
    "MessageResponse",
    # User schemas
    "UserUpdate",
    "UserResponse",
    # Address schemas
    "AddressCreate",
    "AddressUpdate", 
    "AddressResponse",
    "AddressListResponse",
]
