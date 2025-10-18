from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from typing import List
import uuid

# Address schemas
class AddressBase(BaseModel):
    street_line1: str = Field(..., min_length=1, max_length=200, description="Street address line 1")
    street_line2: Optional[str] = Field(None, max_length=200, description="Street address line 2")
    city: str = Field(..., min_length=1, max_length=120, description="City")
    state_region: Optional[str] = Field(None, max_length=120, description="State or region")
    postal_code: str = Field(..., min_length=1, max_length=30, description="Postal code")
    country: str = Field(..., min_length=1, max_length=120, description="Country")
    is_default_shipping: bool = Field(False, description="Is this the default shipping address")

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    street_line1: Optional[str] = Field(None, min_length=1, max_length=200)
    street_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=120)
    state_region: Optional[str] = Field(None, max_length=120)
    postal_code: Optional[str] = Field(None, min_length=1, max_length=30)
    country: Optional[str] = Field(None, min_length=1, max_length=120)
    is_default_shipping: Optional[bool] = None

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
