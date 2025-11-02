from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

# Forward references - will be resolved by model_rebuild()
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.schemas.auction import Auction
    from app.schemas.catalogue import CatalogueItem
    from app.schemas.user import UserRef
    from app.schemas.address import AddressResponse


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class ShippingMethod(str, Enum):
    NORMAL = "NORMAL"
    EXPEDITED = "EXPEDITED"


class OrderBase(BaseModel):
    auction_id: UUID = Field(..., description="ID of the auction for this order")
    buyer_id: UUID = Field(..., description="ID of the buyer")
    item_id: UUID = Field(..., description="ID of the catalogue item")
    winning_bid_amount: Decimal = Field(..., description="Winning bid amount")
    shipping_method: ShippingMethod = Field(..., description="Shipping method (NORMAL or EXPEDITED)")
    shipping_cost: Decimal = Field(..., description="Shipping cost")
    total_amount: Decimal = Field(..., description="Total amount (winning_bid_amount + shipping_cost)")
    shipping_address_id: UUID = Field(..., description="ID of the shipping address")
    status: OrderStatus = Field(..., description="Order status")


class Order(OrderBase):
    order_id: UUID
    created_at: datetime
    updated_at: datetime
    # Relationships
    auction: Optional["Auction"] = None
    buyer: Optional["UserRef"] = None
    item: Optional["CatalogueItem"] = None
    shipping_address: Optional["AddressResponse"] = None
    payment: Optional["Payment"] = None
    receipt: Optional["Receipt"] = None
    shipment: Optional["Shipment"] = None

    class Config:
        from_attributes = True


class PaymentStatus(str, Enum):
    INITIATED = "INITIATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(BaseModel):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    currency: str = Field(default="USD", description="Payment currency")
    status: PaymentStatus
    processor: str = Field(..., description="Payment processor name")
    processor_txn_id: Optional[str] = Field(None, description="Processor transaction ID")
    failure_reason: Optional[str] = Field(None, description="Failure reason if payment failed")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Receipt(BaseModel):
    receipt_id: UUID
    order_id: UUID
    issued_at: datetime
    receipt_number: str = Field(..., description="Unique receipt number")
    total_paid: Decimal
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ShipmentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Shipment(BaseModel):
    shipment_id: UUID
    order_id: UUID
    carrier: Optional[str] = Field(None, description="Shipping carrier")
    tracking_number: Optional[str] = Field(None, description="Tracking number")
    estimated_days: int = Field(..., description="Estimated shipping days")
    status: ShipmentStatus
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

