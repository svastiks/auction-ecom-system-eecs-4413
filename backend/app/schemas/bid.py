from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

# Bid status enumeration
class BidStatus(str):
    LEADING = "LEADING"  # User's bid is the highest
    OUTBID = "OUTBID"    # User has been outbid
    ENDED = "ENDED"      # Auction has ended
    WON = "WON"          # User won the auction

# Response schemas for user's bids
class MyBidItem(BaseModel):
    """Individual bid item in user's bid list."""
    bid_id: uuid.UUID
    auction_id: uuid.UUID
    item_id: uuid.UUID
    item_title: str
    last_bid_amount: Decimal
    current_highest_bid: Decimal
    placed_at: datetime
    time_left_seconds: Optional[int] = None  # None if auction ended
    status: str  # LEADING, OUTBID, ENDED, WON
    auction_status: str  # SCHEDULED, ACTIVE, ENDED, CANCELLED
    auction_end_time: datetime

    class Config:
        from_attributes = True

class MyBidsResponse(BaseModel):
    """Paginated response for user's bids."""
    bids: List[MyBidItem]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int

class BidResponse(BaseModel):
    """Detailed bid information."""
    bid_id: uuid.UUID
    auction_id: uuid.UUID
    bidder_id: uuid.UUID
    amount: Decimal
    placed_at: datetime

    class Config:
        from_attributes = True
