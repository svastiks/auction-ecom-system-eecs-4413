from app.schemas.user import UserRef, UserResponse, UserUpdate
from app.schemas.catalogue import (
    CategoryRead,
    CategoryCreate,
    CategoryUpdate,
    CatalogueItemRead,
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

# ---------------------------------------------------------------------------
# Backward compatibility aliases
# ---------------------------------------------------------------------------

# These aliases prevent older imports from breaking while giving you time
# to update endpoints to use CategoryRead / CatalogueItemRead explicitly.
Category = CategoryRead
CatalogueItem = CatalogueItemRead

# ---------------------------------------------------------------------------
# Optional: rebuild forward refs for models that use self-references
# ---------------------------------------------------------------------------
CategoryRead.model_rebuild()
CatalogueItemRead.model_rebuild()
Auction.model_rebuild()
Bid.model_rebuild()

__all__ = [
    "UserRef",
    "UserResponse",
    "UserUpdate",
    "Category",
    "CategoryRead",
    "CategoryCreate",
    "CategoryUpdate",
    "CatalogueItem",
    "CatalogueItemRead",
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