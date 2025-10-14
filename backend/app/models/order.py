from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Numeric, CheckConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auction_id = Column(UUID(as_uuid=True), ForeignKey("auctions.auction_id"), nullable=False, unique=True)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("catalogue_items.item_id"), nullable=False)
    winning_bid_amount = Column(Numeric(12, 2), nullable=False)
    shipping_method = Column(String, nullable=False)
    shipping_cost = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    shipping_address_id = Column(UUID(as_uuid=True), ForeignKey("addresses.address_id"), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    auction = relationship("Auction", back_populates="order")
    buyer = relationship("User", back_populates="orders")
    item = relationship("CatalogueItem", back_populates="orders")
    shipping_address = relationship("Address", back_populates="orders")
    payment = relationship("Payment", back_populates="order", uselist=False)
    receipt = relationship("Receipt", back_populates="order", uselist=False)
    shipment = relationship("Shipment", back_populates="order", uselist=False)

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("shipping_method IN ('NORMAL','EXPEDITED')", name='ck_shipping_method'),
        CheckConstraint("status IN ('PENDING_PAYMENT','PAID','FAILED','CANCELLED','REFUNDED')", name='ck_order_status'),
        CheckConstraint("total_amount = winning_bid_amount + shipping_cost", name='ck_total_amount'),
        Index('idx_orders_buyer', 'buyer_id'),
    )


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False, unique=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    status = Column(String, nullable=False)
    processor = Column(String, nullable=False)
    processor_txn_id = Column(String)
    failure_reason = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    order = relationship("Order", back_populates="payment")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('INITIATED','AUTHORIZED','CAPTURED','FAILED','REFUNDED')", name='ck_payment_status'),
    )


class Receipt(Base):
    __tablename__ = "receipts"

    receipt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False, unique=True)
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    receipt_number = Column(String(40), unique=True, nullable=False)
    total_paid = Column(Numeric(12, 2), nullable=False)
    notes = Column(String)

    # Relationships
    order = relationship("Order", back_populates="receipt")


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False, unique=True)
    carrier = Column(String)
    tracking_number = Column(String)
    estimated_days = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    shipped_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    order = relationship("Order", back_populates="shipment")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','PROCESSING','SHIPPED','DELIVERED','CANCELLED')", name='ck_shipment_status'),
    )
