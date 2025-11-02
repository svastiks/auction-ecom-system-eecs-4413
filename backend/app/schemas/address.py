from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from typing import List
import uuid
import re

# Address schemas
class AddressBase(BaseModel):
    street_line1: str = Field(..., min_length=1, max_length=200, description="Street address line 1")
    street_line2: Optional[str] = Field(None, max_length=200, description="Street address line 2")
    city: str = Field(..., min_length=1, max_length=120, description="City")
    state_region: Optional[str] = Field(None, max_length=120, description="State or region")
    postal_code: str = Field(..., min_length=1, max_length=30, description="Postal code/ZIP code")
    country: str = Field(..., min_length=1, max_length=120, description="Country")
    phone: Optional[str] = Field(None, max_length=30, description="Phone number for this address")
    is_default_shipping: bool = Field(False, description="Is this the default shipping address")
    
    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        """Validate postal code format - alphanumeric, spaces, and hyphens allowed."""
        if not v:
            return v
        # Allow alphanumeric, spaces, and hyphens (covers US ZIP, Canadian postal codes, etc.)
        if not re.match(r'^[A-Za-z0-9\s\-]+$', v):
            raise ValueError('Postal code must contain only letters, numbers, spaces, and hyphens')
        return v.strip().upper()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if not v:
            return v
        # Allow digits, spaces, parentheses, hyphens, plus sign (international format)
        cleaned = re.sub(r'[\s\(\)\-]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Phone number must be 10-15 digits, optionally with country code (+)')
        return v

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    street_line1: Optional[str] = Field(None, min_length=1, max_length=200)
    street_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=120)
    state_region: Optional[str] = Field(None, max_length=120)
    postal_code: Optional[str] = Field(None, min_length=1, max_length=30)
    country: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    is_default_shipping: Optional[bool] = None
    
    @field_validator('postal_code')
    @classmethod
    def validate_postal_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate postal code format."""
        if not v:
            return v
        if not re.match(r'^[A-Za-z0-9\s\-]+$', v):
            raise ValueError('Postal code must contain only letters, numbers, spaces, and hyphens')
        return v.strip().upper()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if not v:
            return v
        cleaned = re.sub(r'[\s\(\)\-]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Phone number must be 10-15 digits, optionally with country code (+)')
        return v

class AddressResponse(AddressBase):
    address_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AddressListResponse(BaseModel):
    addresses: List[AddressResponse]
    total: int
