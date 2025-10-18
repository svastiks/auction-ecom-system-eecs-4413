from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

class AuctionType(str, Enum):
    FORWARD = "FORWARD"


class AuctionStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"


class AuctionBase(BaseModel):
    auction_type: AuctionType = Field(..., description="Type of auction (FORWARD)")
    starting_price: Decimal = Field(..., description="Starting price for the auction")
    min_increment: Decimal = Field(1.00, description="Minimum bid increment")
    start_time: datetime = Field(..., description="Auction start time")
    end_time: datetime = Field(..., description="Auction end time")
    status: AuctionStatus = Field(AuctionStatus.SCHEDULED, description="Auction status")

    @field_validator("end_time")
    @classmethod
    def end_time_must_be_after_start_time(cls, v, info):
        start_time = info.data.get("start_time")
        if start_time and v <= start_time:
            raise ValueError("End time must be after start time")
        return v


class AuctionCreate(AuctionBase):
    item_id: UUID = Field(..., description="ID of the catalogue item being auctioned")


class AuctionUpdate(BaseModel):
    auction_type: Optional[AuctionType] = None
    starting_price: Optional[Decimal] = None
    min_increment: Optional[Decimal] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AuctionStatus] = None


class BidBase(BaseModel):
    amount: Decimal = Field(..., description="Bid amount")


class BidCreate(BidBase):
    auction_id: UUID = Field(..., description="ID of the auction to bid on")


class Bid(BidBase):
    bid_id: UUID
    auction_id: UUID
    bidder_id: UUID
    placed_at: datetime
    bidder: Optional["UserRef"] = None

    class Config:
        from_attributes = True


class Auction(AuctionBase):
    auction_id: UUID
    item_id: UUID
    winning_bid_id: Optional[UUID] = None
    winning_bidder_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    item: Optional["CatalogueItem"] = None
    winning_bidder: Optional["UserRef"] = None
    bids: List[Bid] = []
    current_highest_bid: Optional[Decimal] = None
    current_highest_bidder_id: Optional[UUID] = None
    remaining_time_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class AuctionItemSummary(BaseModel):
    auction_id: UUID
    item_id: UUID
    title: str
    description: Optional[str]
    current_bidding_price: Decimal
    auction_type: str
    remaining_time_seconds: Optional[int]
    status: str
    item_images: List[str] = []
    seller_name: str
    category_name: Optional[str] = None
    current_highest_bidder_id: Optional[UUID] = None
    current_highest_bidder_name: Optional[str] = None

    class Config:
        from_attributes = True


class AuctionSearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1, description="Search keyword")
    category_id: Optional[UUID] = Field(None, description="Filter by category")
    min_price: Optional[Decimal] = Field(None, description="Minimum current bid price")
    max_price: Optional[Decimal] = Field(None, description="Maximum current bid price")
    status: Optional[AuctionStatus] = Field(
        AuctionStatus.ACTIVE, description="Auction status filter"
    )
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")


class AuctionSearchResponse(BaseModel):
    items: List[AuctionItemSummary]
    total_count: int
    has_more: bool


class BidRequest(BaseModel):
    auction_id: UUID = Field(..., description="ID of the auction to bid on")
    amount: Decimal = Field(..., description="Bid amount")


class BidResponse(BaseModel):
    bid_id: UUID
    auction_id: UUID
    amount: Decimal
    placed_at: datetime
    is_winning_bid: bool
    current_highest_bid: Decimal
    current_highest_bidder_id: UUID
    message: str


class AuctionEndResponse(BaseModel):
    auction_id: UUID
    status: str
    winning_bid_id: Optional[UUID]
    winning_bidder_id: Optional[UUID]
    final_price: Optional[Decimal]
    message: str
    can_pay: bool = False