from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum
import re


class ShippingMethod(str, Enum):
    NORMAL = "NORMAL"
    EXPEDITED = "EXPEDITED"


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, Enum):
    INITIATED = "INITIATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class ShipmentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Order Schemas
class OrderBase(BaseModel):
    shipping_method: ShippingMethod = Field(..., description="Shipping method")
    shipping_address_id: UUID = Field(..., description="Shipping address ID")


class OrderCreate(OrderBase):
    auction_id: UUID = Field(..., description="Auction ID to create order for")


class OrderResponse(BaseModel):
    order_id: UUID
    auction_id: UUID
    buyer_id: UUID
    item_id: UUID
    winning_bid_amount: Decimal
    shipping_method: str
    shipping_cost: Decimal
    total_amount: Decimal
    shipping_address_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderDetail(OrderResponse):
    payment: Optional["PaymentResponse"] = None
    receipt: Optional["ReceiptResponse"] = None
    shipment: Optional["ShipmentResponse"] = None

    class Config:
        from_attributes = True


# Payment Schemas
class PaymentRequest(BaseModel):
    card_number: str = Field(..., description="Credit card number")
    card_holder_name: str = Field(..., description="Card holder name")
    expiry_month: int = Field(..., ge=1, le=12, description="Expiry month (1-12)")
    expiry_year: int = Field(..., ge=2024, description="Expiry year")
    cvv: str = Field(..., description="CVV code")

    @field_validator("card_number")
    @classmethod
    def card_number_exact_digits(cls, v: str) -> str:
        # Extract only digits from the card number
        digits = re.sub(r'\D', '', v)
        if len(digits) != 16:
            raise ValueError("Card number must be exactly 16 digits")
        return digits

    @field_validator("cvv")
    @classmethod
    def cvv_exact_digits(cls, v: str) -> str:
        # Extract only digits from the CVV
        digits = re.sub(r'\D', '', v)
        if len(digits) != 3:
            raise ValueError("CVV must be exactly 3 digits")
        return digits

    @field_validator("card_holder_name")
    @classmethod
    def card_holder_name_no_numbers(cls, v: str) -> str:
        if re.search(r'\d', v):
            raise ValueError("Card holder name cannot contain numbers")
        return v


class PaymentResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    currency: str
    status: str
    processor: str
    processor_txn_id: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentResponseDetail(PaymentResponse):
    order: Optional[OrderResponse] = None

    class Config:
        from_attributes = True


# Receipt Schemas
class ReceiptResponse(BaseModel):
    receipt_id: UUID
    order_id: UUID
    receipt_number: str
    total_paid: Decimal
    issued_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# Shipment Schemas
class ShipmentResponse(BaseModel):
    shipment_id: UUID
    order_id: UUID
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_days: int
    status: str
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Shipping Method Update
class ShippingMethodUpdate(BaseModel):
    shipping_method: ShippingMethod = Field(..., description="New shipping method")


# Pay Response
class PayResponse(BaseModel):
    order_id: UUID
    payment_id: UUID
    status: str
    message: str
    total_amount: Decimal


# Update forward references
OrderDetail.model_rebuild()
PaymentResponseDetail.model_rebuild()

