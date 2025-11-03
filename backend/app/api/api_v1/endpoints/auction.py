from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, select, func
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal
from datetime import timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.auction import Auction, Bid
from app.models.catalogue import CatalogueItem, Category, ItemImage
from app.models.user import User
from app.schemas.auction import (
    Auction as AuctionSchema,
    AuctionCreate,
    AuctionUpdate,
    AuctionItemSummary,
    AuctionSearchRequest,
    AuctionSearchResponse,
    BidRequest,
    BidResponse,
    Bid as BidSchema,
    AuctionEndResponse,
    AuctionStatus,
    AuctionType,
)

router = APIRouter()


def get_current_bidding_price(auction: Auction) -> Decimal:
    """Calculate current bidding price for an auction."""
    if not auction.bids:
        return auction.starting_price
    return max(bid.amount for bid in auction.bids)


def get_remaining_time(auction: Auction) -> Optional[int]:
    """Calculate remaining time in seconds for an auction."""
    if auction.status != AuctionStatus.ACTIVE:
        return None
    now = datetime.now(timezone.utc)
    if auction.end_time <= now:
        return 0
    return int((auction.end_time - now).total_seconds())


# Auction Management Endpoints
@router.post("", response_model=AuctionSchema, status_code=status.HTTP_201_CREATED)
async def create_auction(
    auction_data: AuctionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new auction for a catalogue item.
    Only the seller of the item can create an auction for it.
    """
    # Check if item exists
    item = db.query(CatalogueItem).filter(CatalogueItem.item_id == auction_data.item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalogue item not found"
        )
    
    # Check if user is the seller
    if item.seller_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can create an auction for their item"
        )
    
    # Check if auction already exists for this item
    existing_auction = db.query(Auction).filter(Auction.item_id == auction_data.item_id).first()
    if existing_auction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An auction already exists for this item"
        )
    
    # Check if start time is in the past
    now = datetime.now(timezone.utc)
    if auction_data.end_time <= now:
        # Auction end time is already in the past - mark as ended
        status_value = AuctionStatus.ENDED
    elif auction_data.start_time <= now:
        # Auto-activate if start time has passed (but end_time is in future)
        status_value = AuctionStatus.ACTIVE
    else:
        status_value = auction_data.status
    
    # Create auction
    auction = Auction(
        item_id=auction_data.item_id,
        auction_type=auction_data.auction_type,
        starting_price=auction_data.starting_price,
        min_increment=auction_data.min_increment,
        start_time=auction_data.start_time,
        end_time=auction_data.end_time,
        status=status_value
    )
    
    db.add(auction)
    db.commit()
    db.refresh(auction)
    
    return auction


# UC2: Browse Catalogue Endpoints
@router.post("/search", response_model=AuctionSearchResponse)
async def search_auctions(
    search_request: AuctionSearchRequest,
    db: Session = Depends(get_db)
):
    """
    UC2.1: Search for auctioned items by keyword.
    Returns list of items up for auction matching the keywords.
    """
    # Base query with joins
    query = db.query(Auction).join(CatalogueItem).join(User, CatalogueItem.seller_id == User.user_id).options(
        joinedload(Auction.item).joinedload(CatalogueItem.seller),
        joinedload(Auction.item).joinedload(CatalogueItem.category),
        joinedload(Auction.item).joinedload(CatalogueItem.images),
        joinedload(Auction.bids)
    )
    
    # Status filter
    if search_request.status:
        query = query.filter(Auction.status == search_request.status.value)
    
    # Keyword search in item title, description, and keywords
    if search_request.keyword:
        keyword_filter = or_(
            CatalogueItem.title.ilike(f"%{search_request.keyword}%"),
            CatalogueItem.description.ilike(f"%{search_request.keyword}%"),
            CatalogueItem.keywords.ilike(f"%{search_request.keyword}%")
        )
        query = query.filter(keyword_filter)
    
    # Category filter
    if search_request.category_id:
        query = query.filter(CatalogueItem.category_id == search_request.category_id)
    
    # Get all results for price filtering
    all_auctions = query.all()
    
    # Filter by price range
    filtered_auctions = []
    for auction in all_auctions:
        current_price = get_current_bidding_price(auction)
        
        if search_request.min_price and current_price < search_request.min_price:
            continue
        if search_request.max_price and current_price > search_request.max_price:
            continue
        
        filtered_auctions.append(auction)
    
    # Get total count before pagination
    total_count = len(filtered_auctions)
    
    # Pagination
    paginated_auctions = filtered_auctions[search_request.skip:search_request.skip + search_request.limit]
    
    # Build response items
    items = []
    for auction in paginated_auctions:
        current_price = get_current_bidding_price(auction)
        remaining_time = get_remaining_time(auction)
        
        # Get highest bidder
        highest_bid = None
        if auction.bids:
            highest_bid = max(auction.bids, key=lambda b: b.amount)
        
        # Get images
        images = [img.url for img in sorted(auction.item.images, key=lambda i: i.position)]
        
        items.append(AuctionItemSummary(
            auction_id=auction.auction_id,
            item_id=auction.item.item_id,
            title=auction.item.title,
            description=auction.item.description,
            current_bidding_price=current_price,
            auction_type=auction.auction_type,
            remaining_time_seconds=remaining_time,
            status=auction.status,
            item_images=images,
            seller_name=f"{auction.item.seller.first_name} {auction.item.seller.last_name}",
            category_name=auction.item.category.name if auction.item.category else None,
            current_highest_bidder_id=highest_bid.bidder_id if highest_bid else None,
            current_highest_bidder_name=f"{highest_bid.bidder.first_name} {highest_bid.bidder.last_name}" if highest_bid and highest_bid.bidder else None
        ))
    
    return AuctionSearchResponse(
        items=items,
        total_count=total_count,
        has_more=(search_request.skip + search_request.limit) < total_count
    )


@router.get("/items/{item_id}", response_model=AuctionItemSummary)
async def get_auction_item_detail(
    item_id: UUID,
    db: Session = Depends(get_db)
):
    """
    UC2.2 & UC2.3: Get detailed information about a specific auctioned item.
    Displays full item details for bidding.
    """
    auction = db.query(Auction).join(CatalogueItem).options(
        joinedload(Auction.item).joinedload(CatalogueItem.seller),
        joinedload(Auction.item).joinedload(CatalogueItem.category),
        joinedload(Auction.item).joinedload(CatalogueItem.images),
        joinedload(Auction.bids).joinedload(Bid.bidder)
    ).filter(Auction.item_id == item_id).first()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    current_price = get_current_bidding_price(auction)
    remaining_time = get_remaining_time(auction)
    
    # Get highest bidder
    highest_bid = None
    if auction.bids:
        highest_bid = max(auction.bids, key=lambda b: b.amount)
    
    # Get images
    images = [img.url for img in sorted(auction.item.images, key=lambda i: i.position)]
    
    return AuctionItemSummary(
        auction_id=auction.auction_id,
        item_id=auction.item.item_id,
        title=auction.item.title,
        description=auction.item.description,
        current_bidding_price=current_price,
        auction_type=auction.auction_type,
        remaining_time_seconds=remaining_time,
        status=auction.status,
        item_images=images,
        seller_name=f"{auction.item.seller.first_name} {auction.item.seller.last_name}",
        category_name=auction.item.category.name if auction.item.category else None,
        current_highest_bidder_id=highest_bid.bidder_id if highest_bid else None,
        current_highest_bidder_name=f"{highest_bid.bidder.first_name} {highest_bid.bidder.last_name}" if highest_bid and highest_bid.bidder else None
    )


@router.get("/{auction_id}", response_model=AuctionSchema)
async def get_auction(
    auction_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed auction information including all bids."""
    auction = db.query(Auction).options(
        joinedload(Auction.item).joinedload(CatalogueItem.seller),
        joinedload(Auction.item).joinedload(CatalogueItem.category),
        joinedload(Auction.item).joinedload(CatalogueItem.images),
        joinedload(Auction.bids).joinedload(Bid.bidder),
        joinedload(Auction.winning_bidder)
    ).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Calculate current highest bid
    current_highest_bid = get_current_bidding_price(auction)
    
    # Get highest bidder
    highest_bid = None
    if auction.bids:
        highest_bid = max(auction.bids, key=lambda b: b.amount)
    
    remaining_time = get_remaining_time(auction)
    
    return AuctionSchema(
        auction_id=auction.auction_id,
        item_id=auction.item_id,
        auction_type=auction.auction_type,
        starting_price=auction.starting_price,
        min_increment=auction.min_increment,
        start_time=auction.start_time,
        end_time=auction.end_time,
        status=auction.status,
        winning_bid_id=auction.winning_bid_id,
        winning_bidder_id=auction.winning_bidder_id,
        created_at=auction.created_at,
        updated_at=auction.updated_at,
        item=auction.item,
        winning_bidder=auction.winning_bidder,
        bids=auction.bids,
        current_highest_bid=current_highest_bid,
        current_highest_bidder_id=highest_bid.bidder_id if highest_bid else None,
        remaining_time_seconds=remaining_time
    )


# UC3: Bidding Endpoints
@router.post("/bid", response_model=BidResponse)
async def place_bid(
    bid_request: BidRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    UC3: Place a bid on an auction.
    Bidding price must be higher than the current price.
    """
    # Get auction with bids
    auction = db.query(Auction).options(
        joinedload(Auction.bids),
        joinedload(Auction.item)
    ).filter(Auction.auction_id == bid_request.auction_id).first()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if auction has ended (check end_time first and update status if needed)
    now = datetime.now(timezone.utc)
    if auction.end_time <= now:
        # Update status to ENDED if it hasn't been updated yet
        if auction.status != AuctionStatus.ENDED:
            auction.status = AuctionStatus.ENDED
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has ended"
        )
    
    # Auto-activate auction if start_time has passed
    if auction.start_time <= now and auction.status == AuctionStatus.SCHEDULED:
        auction.status = AuctionStatus.ACTIVE
        db.commit()
    
    # Check if auction hasn't started yet
    if auction.start_time > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has not started yet"
        )
    
    # Check auction status
    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot bid on {auction.status.lower()} auction"
        )
    
    # Get current bidding price
    current_price = get_current_bidding_price(auction)
    
    # Check minimum bid amount
    min_bid = current_price + auction.min_increment
    
    if bid_request.amount < min_bid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid must be at least ${min_bid:.2f} (current: ${current_price:.2f}, increment: ${auction.min_increment:.2f})"
        )
    
    # Check if user is the seller
    if auction.item.seller_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot bid on your own item"
        )
    
    # Create bid
    bid = Bid(
        auction_id=auction.auction_id,
        bidder_id=current_user.user_id,
        amount=bid_request.amount
    )
    db.add(bid)
    
    # Update auction
    auction.updated_at = now
    
    db.commit()
    db.refresh(bid)
    
    # Return response
    return BidResponse(
        bid_id=bid.bid_id,
        auction_id=bid.auction_id,
        amount=bid.amount,
        placed_at=bid.placed_at,
        is_winning_bid=True,
        current_highest_bid=bid.amount,
        current_highest_bidder_id=current_user.user_id,
        message="Bid placed successfully"
    )


@router.get("/{auction_id}/bids", response_model=List[BidSchema])
async def get_auction_bids(
    auction_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all bids for an auction, ordered by amount (highest first)."""
    auction = db.query(Auction).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    bids = db.query(Bid).options(
        joinedload(Bid.bidder)
    ).filter(Bid.auction_id == auction_id).order_by(desc(Bid.amount)).all()
    
    return bids


@router.post("/{auction_id}/end", response_model=AuctionEndResponse)
async def end_auction(
    auction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually end an auction and determine the winner.
    Returns auction end information and whether payment is possible.
    """
    auction = db.query(Auction).options(
        joinedload(Auction.bids).joinedload(Bid.bidder)
    ).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Only seller can end auction early
    item = db.query(CatalogueItem).filter(CatalogueItem.item_id == auction.item_id).first()
    if item.seller_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can end the auction"
        )
    
    # Check if already ended
    if auction.status == AuctionStatus.ENDED:
        return AuctionEndResponse(
            auction_id=auction.auction_id,
            status=auction.status,
            winning_bid_id=auction.winning_bid_id,
            winning_bidder_id=auction.winning_bidder_id,
            final_price=get_current_bidding_price(auction) if auction.bids else auction.starting_price,
            message="Auction has already ended",
            can_pay=False
        )
    
    # Update auction status
    auction.status = AuctionStatus.ENDED
    
    # Explicitly query bids to ensure they're loaded
    bids = db.query(Bid).filter(Bid.auction_id == auction_id).order_by(desc(Bid.amount)).all()
    
    # Determine winner if there are bids
    if bids:
        winning_bid = bids[0]  # Already sorted by amount desc, so first is highest
        auction.winning_bid_id = winning_bid.bid_id
        auction.winning_bidder_id = winning_bid.bidder_id
        final_price = winning_bid.amount
        
        # Load bidder info for message
        bidder = db.query(User).filter(User.user_id == winning_bid.bidder_id).first()
        bidder_name = f"{bidder.first_name} {bidder.last_name}" if bidder else "Unknown"
        message = f"Auction ended. Winner: {bidder_name}"
    else:
        auction.winning_bid_id = None
        auction.winning_bidder_id = None
        final_price = auction.starting_price
        message = "Auction ended with no bids"
    
    db.commit()
    db.refresh(auction)  # Refresh to ensure all fields are updated
    
    return AuctionEndResponse(
        auction_id=auction.auction_id,
        status=auction.status,
        winning_bid_id=auction.winning_bid_id,
        winning_bidder_id=auction.winning_bidder_id,
        final_price=final_price,
        message=message,
        can_pay=True if bids else False
    )


@router.get("/{auction_id}/status", response_model=AuctionEndResponse)
async def get_auction_status(
    auction_id: UUID,
    db: Session = Depends(get_db)
):
    """Check auction status to see if it has ended."""
    auction = db.query(Auction).options(
        joinedload(Auction.bids).joinedload(Bid.bidder)
    ).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    
    # Check if auction should be automatically ended
    now = datetime.now(timezone.utc)
    if auction.status == AuctionStatus.ACTIVE and auction.end_time <= now:
        auction.status = AuctionStatus.ENDED
        
        # Explicitly query bids to ensure they're loaded
        bids = db.query(Bid).filter(Bid.auction_id == auction_id).order_by(desc(Bid.amount)).all()
        
        if bids:
            winning_bid = bids[0]  # Already sorted by amount desc, so first is highest
            auction.winning_bid_id = winning_bid.bid_id
            auction.winning_bidder_id = winning_bid.bidder_id
            final_price = winning_bid.amount
            
            # Load bidder info for message
            bidder = db.query(User).filter(User.user_id == winning_bid.bidder_id).first()
            bidder_name = f"{bidder.first_name} {bidder.last_name}" if bidder else "Unknown"
            message = f"Auction ended. Winner: {bidder_name}"
        else:
            auction.winning_bid_id = None
            auction.winning_bidder_id = None
            final_price = auction.starting_price
            message = "Auction ended with no bids"
        
        db.commit()
        db.refresh(auction)  # Refresh to ensure all fields are updated
    
    return AuctionEndResponse(
        auction_id=auction.auction_id,
        status=auction.status,
        winning_bid_id=auction.winning_bid_id,
        winning_bidder_id=auction.winning_bidder_id,
        final_price=get_current_bidding_price(auction) if auction.bids or auction.status == AuctionStatus.ENDED else None,
        message="Auction is active" if auction.status == AuctionStatus.ACTIVE else "Auction has ended",
        can_pay=True if auction.status == AuctionStatus.ENDED and auction.bids else False
    )