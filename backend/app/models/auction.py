from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Auction(Base):
    __tablename__ = "auctions"

    auction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("catalogue_items.item_id"), nullable=False, unique=True)
    auction_type = Column(String, nullable=False)
    starting_price = Column(Numeric(12, 2), nullable=False)
    min_increment = Column(Numeric(12, 2), nullable=False, default=1.00)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    winning_bid_id = Column(UUID(as_uuid=True))
    winning_bidder_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    item = relationship("CatalogueItem", foreign_keys=[item_id])
    winning_bidder = relationship("User", back_populates="auctions")
    bids = relationship("Bid", back_populates="auction", cascade="all, delete-orphan")
    order = relationship("Order", back_populates="auction", uselist=False)

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint("auction_type IN ('FORWARD')", name='ck_auction_type'),
        CheckConstraint("status IN ('SCHEDULED','ACTIVE','ENDED','CANCELLED')", name='ck_auction_status'),
        CheckConstraint("end_time > start_time", name='ck_auction_times'),
        Index('idx_auctions_status_end', 'status', 'end_time'),
    )


class Bid(Base):
    __tablename__ = "bids"

    bid_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auction_id = Column(UUID(as_uuid=True), ForeignKey("auctions.auction_id", ondelete="CASCADE"), nullable=False)
    bidder_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    placed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    auction = relationship("Auction", back_populates="bids")
    bidder = relationship("User", back_populates="bids")

    # Indexes
    __table_args__ = (
        Index('idx_bids_auction_amount', 'auction_id', 'amount'),
        Index('idx_bids_auction_time', 'auction_id', 'placed_at'),
        Index('idx_bids_bidder', 'bidder_id'),
    )
