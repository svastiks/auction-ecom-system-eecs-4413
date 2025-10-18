from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
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
    Bid as BidSchema,
    BidCreate,
    BidRequest,
    BidResponse,
    AuctionEndResponse,
    AuctionStatus,
    AuctionType
)

router = APIRouter()


# UC3: Bidding Endpoints
@router.post("/bid", response_model=BidResponse)
def place_bid(
    bid_request: BidRequest, 
    session_id: str = Query(..., description="User session ID for tracking"),
    bidder_id: UUID = Query(..., description="Bidder user ID"),  # TODO: Get from auth token
    db: Session = Depends(get_db)
):
    """
    UC3: Place a bid on an auction
    - Validates bid amount is higher than current highest bid
    - Enforces one bid per session per item rule
    - Updates auction with new highest bidder
    - Returns bid confirmation with current auction status
    """
    # Get auction with current highest bid
    auction = db.query(Auction).options(
        joinedload(Auction.bids).joinedload(Bid.bidder)
    ).filter(Auction.auction_id == bid_request.auction_id).first()
    
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Check if auction is active
    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Auction is not active")
    
    # Check if auction has ended
    if datetime.utcnow() > auction.end_time:
        raise HTTPException(status_code=400, detail="Auction has ended")
    
    # UC3: Check if user has already bid on this item in this session
    existing_bid = db.query(Bid).filter(
        and_(
            Bid.auction_id == bid_request.auction_id,
            Bid.bidder_id == bidder_id
        )
    ).first()
    
    if existing_bid:
        raise HTTPException(
            status_code=400, 
            detail="You have already placed a bid on this item in your current session. Only one bid per item per session is allowed."
        )
    
    # Get current highest bid
    current_highest_bid = db.query(func.max(Bid.amount)).filter(
        Bid.auction_id == auction.auction_id
    ).scalar() or auction.starting_price
    
    # Validate bid amount
    min_bid = current_highest_bid + auction.min_increment
    if bid_request.amount < min_bid:
        raise HTTPException(
            status_code=400, 
            detail=f"Bid amount must be at least {min_bid} (current highest: {current_highest_bid} + minimum increment: {auction.min_increment})"
        )
    
    # Create new bid
    new_bid = Bid(
        auction_id=bid_request.auction_id,
        bidder_id=bidder_id,
        amount=bid_request.amount
    )
    
    db.add(new_bid)
    db.flush()  # Get bid_id
    
    # Update auction with new highest bidder
    auction.winning_bid_id = new_bid.bid_id
    auction.winning_bidder_id = new_bid.bidder_id
    
    db.commit()
    db.refresh(new_bid)
    
    # Calculate remaining time
    remaining_time = int((auction.end_time - datetime.utcnow()).total_seconds())
    remaining_time = max(0, remaining_time)
    
    # Get bidder info for response
    bidder = db.query(User).filter(User.user_id == new_bid.bidder_id).first()
    bidder_name = f"{bidder.first_name} {bidder.last_name}" if bidder else "Unknown"
    
    return BidResponse(
        bid_id=new_bid.bid_id,
        auction_id=new_bid.auction_id,
        amount=new_bid.amount,
        placed_at=new_bid.placed_at,
        is_winning_bid=True,
        current_highest_bid=new_bid.amount,
        current_highest_bidder_id=new_bid.bidder_id,
        message=f"Bid placed successfully! You ({bidder_name}) are now the highest bidder with ${new_bid.amount}. Time remaining: {remaining_time} seconds."
    )


@router.get("/auctions/{auction_id}/status", response_model=AuctionEndResponse)
def get_auction_status(auction_id: UUID, db: Session = Depends(get_db)):
    """
    UC3: Check auction status and handle auction ending
    - Returns current auction status
    - If auction has ended, provides payment option
    """
    auction = db.query(Auction).options(
        joinedload(Auction.bids).joinedload(Bid.bidder)
    ).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    current_time = datetime.utcnow()
    
    # Check if auction has ended
    if current_time > auction.end_time and auction.status == AuctionStatus.ACTIVE:
        # Update auction status to ENDED
        auction.status = AuctionStatus.ENDED
        db.commit()
        
        return AuctionEndResponse(
            auction_id=auction.auction_id,
            status=auction.status,
            winning_bid_id=auction.winning_bid_id,
            winning_bidder_id=auction.winning_bidder_id,
            final_price=auction.winning_bid_id and db.query(Bid.amount).filter(
                Bid.bid_id == auction.winning_bid_id
            ).scalar(),
            message="Auction has ended!",
            can_pay=auction.winning_bid_id is not None
        )
    
    # Calculate remaining time
    remaining_time = int((auction.end_time - current_time).total_seconds())
    remaining_time = max(0, remaining_time)
    
    return AuctionEndResponse(
        auction_id=auction.auction_id,
        status=auction.status,
        winning_bid_id=auction.winning_bid_id,
        winning_bidder_id=auction.winning_bidder_id,
        final_price=None,
        message=f"Auction is {auction.status.lower()}. Time remaining: {remaining_time} seconds",
        can_pay=False
    )


# UC2: Browse Catalogue Endpoints
@router.get("/search", response_model=AuctionSearchResponse)
def search_auctioned_items(
    keyword: str = Query(..., min_length=1, description="Search keyword"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, description="Minimum current bid price"),
    max_price: Optional[Decimal] = Query(None, description="Maximum current bid price"),
    status: Optional[AuctionStatus] = Query(AuctionStatus.ACTIVE, description="Auction status filter"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    db: Session = Depends(get_db)
):
    """
    UC2.1: Item Search - Search for auctioned items by keyword
    Returns list of items matching keywords with current bid info
    """
    # Build base query with joins
    query = db.query(Auction).options(
        joinedload(Auction.item).joinedload(CatalogueItem.category),
        joinedload(Auction.item).joinedload(CatalogueItem.seller),
        joinedload(Auction.item).joinedload(CatalogueItem.images)
    ).join(CatalogueItem, Auction.item_id == CatalogueItem.item_id)
    
    # Apply status filter
    if status:
        query = query.filter(Auction.status == status)
    
    # Apply category filter
    if category_id:
        query = query.filter(CatalogueItem.category_id == category_id)
    
    # Apply price filters
    if min_price is not None or max_price is not None:
        # Get current highest bids for price filtering
        subquery = db.query(
            Bid.auction_id,
            func.max(Bid.amount).label('current_bid')
        ).group_by(Bid.auction_id).subquery()
        
        query = query.outerjoin(subquery, Auction.auction_id == subquery.c.auction_id)
        
        if min_price is not None:
            query = query.filter(
                or_(
                    subquery.c.current_bid >= min_price,
                    and_(subquery.c.current_bid.is_(None), Auction.starting_price >= min_price)
                )
            )
        
        if max_price is not None:
            query = query.filter(
                or_(
                    subquery.c.current_bid <= max_price,
                    and_(subquery.c.current_bid.is_(None), Auction.starting_price <= max_price)
                )
            )
    
    # Apply keyword search
    if keyword:
        keyword_filter = or_(
            CatalogueItem.title.ilike(f"%{keyword}%"),
            CatalogueItem.description.ilike(f"%{keyword}%"),
            CatalogueItem.keywords.ilike(f"%{keyword}%")
        )
        query = query.filter(keyword_filter)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    auctions = query.offset(skip).limit(limit).all()
    
    # Convert to summary format
    items = []
    for auction in auctions:
        # Get current highest bid and bidder
        highest_bid_info = db.query(
            Bid.amount,
            Bid.bidder_id,
            User.first_name,
            User.last_name
        ).join(User, Bid.bidder_id == User.user_id).filter(
            Bid.auction_id == auction.auction_id
        ).order_by(desc(Bid.amount)).first()
        
        if highest_bid_info:
            current_bid = highest_bid_info.amount
            current_bidder_id = highest_bid_info.bidder_id
            current_bidder_name = f"{highest_bid_info.first_name} {highest_bid_info.last_name}"
        else:
            current_bid = auction.starting_price
            current_bidder_id = None
            current_bidder_name = None
        
        # Calculate remaining time
        remaining_time = int((auction.end_time - datetime.utcnow()).total_seconds())
        remaining_time = max(0, remaining_time) if auction.status == AuctionStatus.ACTIVE else None
        
        # Get item images
        item_images = [img.url for img in auction.item.images] if auction.item.images else []
        
        items.append(AuctionItemSummary(
            auction_id=auction.auction_id,
            item_id=auction.item_id,
            title=auction.item.title,
            description=auction.item.description,
            current_bidding_price=current_bid,
            auction_type=auction.auction_type,
            remaining_time_seconds=remaining_time,
            status=auction.status,
            item_images=item_images,
            seller_name=f"{auction.item.seller.first_name} {auction.item.seller.last_name}",
            category_name=auction.item.category.name if auction.item.category else None,
            current_highest_bidder_id=current_bidder_id,
            current_highest_bidder_name=current_bidder_name
        ))
    
    return AuctionSearchResponse(
        items=items,
        total_count=total_count,
        has_more=(skip + len(items)) < total_count
    )


@router.post("/items/{auction_id}/select")
def select_item_for_bidding(auction_id: UUID, db: Session = Depends(get_db)):
    """
    UC2.3: Item Selection - Select an item for bidding
    This endpoint handles the radio button selection and prepares for bidding
    Returns item details and bidding form data
    """
    auction = db.query(Auction).options(
        joinedload(Auction.item).joinedload(CatalogueItem.category),
        joinedload(Auction.item).joinedload(CatalogueItem.seller),
        joinedload(Auction.item).joinedload(CatalogueItem.images)
    ).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Check if auction is active
    if auction.status != AuctionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Auction is not active")
    
    # Get current highest bid and bidder
    highest_bid_info = db.query(
        Bid.amount,
        Bid.bidder_id,
        User.first_name,
        User.last_name
    ).join(User, Bid.bidder_id == User.user_id).filter(
        Bid.auction_id == auction.auction_id
    ).order_by(desc(Bid.amount)).first()
    
    if highest_bid_info:
        current_bid = highest_bid_info.amount
        current_bidder_id = highest_bid_info.bidder_id
        current_bidder_name = f"{highest_bid_info.first_name} {highest_bid_info.last_name}"
    else:
        current_bid = auction.starting_price
        current_bidder_id = None
        current_bidder_name = None
    
    # Calculate remaining time
    remaining_time = int((auction.end_time - datetime.utcnow()).total_seconds())
    remaining_time = max(0, remaining_time)
    
    # Get item images
    item_images = [img.url for img in auction.item.images] if auction.item.images else []
    
    return {
        "selected": True,
        "auction_id": auction.auction_id,
        "item_details": AuctionItemSummary(
            auction_id=auction.auction_id,
            item_id=auction.item_id,
            title=auction.item.title,
            description=auction.item.description,
            current_bidding_price=current_bid,
            auction_type=auction.auction_type,
            remaining_time_seconds=remaining_time,
            status=auction.status,
            item_images=item_images,
            seller_name=f"{auction.item.seller.first_name} {auction.item.seller.last_name}",
            category_name=auction.item.category.name if auction.item.category else None,
            current_highest_bidder_id=current_bidder_id,
            current_highest_bidder_name=current_bidder_name
        ),
        "bidding_info": {
            "min_bid_amount": current_bid + auction.min_increment,
            "min_increment": auction.min_increment,
            "auction_type": auction.auction_type
        },
        "message": "Item selected for bidding. You can now place a bid."
    }


@router.get("/items/{auction_id}/details", response_model=AuctionItemSummary)
def get_auction_item_details(auction_id: UUID, db: Session = Depends(get_db)):
    """
    UC2.2: Display Auctioned Items - Get detailed info for a specific auctioned item
    Shows full item details, current bid, auction type, and remaining time
    """
    auction = db.query(Auction).options(
        joinedload(Auction.item).joinedload(CatalogueItem.category),
        joinedload(Auction.item).joinedload(CatalogueItem.seller),
        joinedload(Auction.item).joinedload(CatalogueItem.images)
    ).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Get current highest bid
    current_bid = db.query(func.max(Bid.amount)).filter(
        Bid.auction_id == auction.auction_id
    ).scalar() or auction.starting_price
    
    # Calculate remaining time
    remaining_time = int((auction.end_time - datetime.utcnow()).total_seconds())
    remaining_time = max(0, remaining_time) if auction.status == AuctionStatus.ACTIVE else None
    
    # Get item images
    item_images = [img.url for img in auction.item.images] if auction.item.images else []
    
    return AuctionItemSummary(
        auction_id=auction.auction_id,
        item_id=auction.item_id,
        title=auction.item.title,
        description=auction.item.description,
        current_bidding_price=current_bid,
        auction_type=auction.auction_type,
        remaining_time_seconds=remaining_time,
        status=auction.status,
        item_images=item_images,
        seller_name=f"{auction.item.seller.first_name} {auction.item.seller.last_name}",
        category_name=auction.item.category.name if auction.item.category else None
    )


# Additional utility endpoints
@router.get("/auctions", response_model=List[AuctionSchema])
def get_auctions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AuctionStatus] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all auctions with optional filtering"""
    query = db.query(Auction).options(
        joinedload(Auction.item),
        joinedload(Auction.bids)
    )
    
    if status:
        query = query.filter(Auction.status == status)
    
    auctions = query.offset(skip).limit(limit).all()
    return auctions


@router.get("/auctions/{auction_id}", response_model=AuctionSchema)
def get_auction(auction_id: UUID, db: Session = Depends(get_db)):
    """Get a specific auction by ID"""
    auction = db.query(Auction).options(
        joinedload(Auction.item),
        joinedload(Auction.bids).joinedload(Bid.bidder)
    ).filter(Auction.auction_id == auction_id).first()
    
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    return auction


@router.post("/auctions", response_model=AuctionSchema)
def create_auction(auction: AuctionCreate, db: Session = Depends(get_db)):
    """Create a new auction"""
    # Check if item exists and is not already auctioned
    existing_auction = db.query(Auction).filter(Auction.item_id == auction.item_id).first()
    if existing_auction:
        raise HTTPException(status_code=400, detail="Item is already being auctioned")
    
    db_auction = Auction(**auction.dict())
    db.add(db_auction)
    db.commit()
    db.refresh(db_auction)
    return db_auction
