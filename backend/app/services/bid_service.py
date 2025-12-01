from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from datetime import datetime, timezone
from app.models.auction import Bid, Auction
from app.models.catalogue import CatalogueItem
from app.schemas.bid import MyBidItem, MyBidsResponse
from decimal import Decimal
import uuid
import math

class BidService:
    def __init__(self, db: Session):
        self.db = db

    async def get_my_bids(
        self, 
        user_id: uuid.UUID, 
        page: int = 1, 
        page_size: int = 20
    ) -> MyBidsResponse:
        """Get all bids for a user with status information."""
        
        # Get all bids for the user, ordered by most recent first
        stmt = (
            select(Bid, Auction, CatalogueItem)
            .join(Auction, Bid.auction_id == Auction.auction_id)
            .join(CatalogueItem, Auction.item_id == CatalogueItem.item_id)
            .where(Bid.bidder_id == user_id)
            .order_by(desc(Bid.placed_at))
        )
        
        result = self.db.execute(stmt).all()
        
        # Process bids to determine status
        bid_items = []
        for bid, auction, item in result:
            status, current_highest = self._determine_bid_status(bid, auction)
            time_left = self._calculate_time_left(auction)
            
            bid_item = MyBidItem(
                bid_id=bid.bid_id,
                auction_id=auction.auction_id,
                item_id=item.item_id,
                item_title=item.title,
                last_bid_amount=bid.amount,
                current_highest_bid=current_highest,
                placed_at=bid.placed_at,
                time_left_seconds=time_left,
                status=status,
                auction_status=auction.status,
                auction_end_time=auction.end_time
            )
            bid_items.append(bid_item)
        
        # Pagination
        total = len(bid_items)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_bids = bid_items[start_idx:end_idx]
        
        return MyBidsResponse(
            bids=paginated_bids,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def _determine_bid_status(self, bid: Bid, auction: Auction) -> Tuple[str, Decimal]:
        """Determine the status of a bid (LEADING, OUTBID, ENDED, WON) and current highest bid."""
        now = datetime.now(timezone.utc)
        
        # If auction has ended
        if auction.status == "ENDED":
            # Check if this user won
            if auction.winning_bidder_id == bid.bidder_id:
                # Get the highest bid amount (could be winning bid or their bid if they won)
                highest_bid_stmt = (
                    select(func.max(Bid.amount))
                    .where(Bid.auction_id == auction.auction_id)
                )
                highest_bid = self.db.execute(highest_bid_stmt).scalar() or bid.amount
                return "WON", highest_bid
            else:
                # Auction ended but user didn't win
                highest_bid_stmt = (
                    select(func.max(Bid.amount))
                    .where(Bid.auction_id == auction.auction_id)
                )
                highest_bid = self.db.execute(highest_bid_stmt).scalar() or bid.amount
                return "ENDED", highest_bid
        
        # If auction is cancelled or not active
        if auction.status != "ACTIVE":
            highest_bid_stmt = (
                select(func.max(Bid.amount))
                .where(Bid.auction_id == auction.auction_id)
            )
            highest_bid = self.db.execute(highest_bid_stmt).scalar() or bid.amount
            return "ENDED", highest_bid
        
        # Auction is active - check if this bid is leading
        # Get the highest bid for this auction
        highest_bid_stmt = (
            select(Bid)
            .where(Bid.auction_id == auction.auction_id)
            .order_by(desc(Bid.amount))
            .limit(1)
        )
        highest_bid_result = self.db.execute(highest_bid_stmt).scalar_one_or_none()
        
        if highest_bid_result:
            highest_bid = highest_bid_result.amount
            
            # Check if this user's bid is the highest
            if highest_bid_result.bidder_id == bid.bidder_id and highest_bid_result.bid_id == bid.bid_id:
                return "LEADING", highest_bid
            else:
                return "OUTBID", highest_bid
        else:
            # No bids found (shouldn't happen, but handle it)
            return "LEADING", bid.amount

    def _ensure_timezone_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (UTC)."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    def _calculate_time_left(self, auction: Auction) -> Optional[int]:
        """Calculate time left in seconds for an active auction. Returns None if ended."""
        now = datetime.now(timezone.utc)
        end_time = self._ensure_timezone_aware(auction.end_time)
        
        if auction.status != "ACTIVE" or end_time <= now:
            return None
        
        time_delta = end_time - now
        return int(time_delta.total_seconds())
