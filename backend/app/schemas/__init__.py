from app.schemas.user import UserRef, UserResponse, UserUpdate
from app.schemas.catalogue import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CatalogueItem,
    CatalogueItemCreate,
    CatalogueItemUpdate,
    ItemImage,
    ItemImageCreate,
)
from app.schemas.auction import (
    Auction,
    AuctionCreate,
    AuctionUpdate,
    AuctionItemSummary,
    AuctionSearchRequest,
    AuctionSearchResponse,
    Bid,
    BidCreate,
    BidRequest,
    BidResponse,
    AuctionEndResponse,
    AuctionStatus,
    AuctionType,
)

# Rebuild models to resolve forward references
Category.model_rebuild()
CatalogueItem.model_rebuild()
Auction.model_rebuild()
Bid.model_rebuild()

__all__ = [
    "UserRef",
    "UserResponse",
    "UserUpdate",
    "Category",
    "CategoryCreate",
    "CategoryUpdate",
    "CatalogueItem",
    "CatalogueItemCreate",
    "CatalogueItemUpdate",
    "ItemImage",
    "ItemImageCreate",
    "Auction",
    "AuctionCreate",
    "AuctionUpdate",
    "AuctionItemSummary",
    "AuctionSearchRequest",
    "AuctionSearchResponse",
    "Bid",
    "BidCreate",
    "BidRequest",
    "BidResponse",
    "AuctionEndResponse",
    "AuctionStatus",
    "AuctionType",
]