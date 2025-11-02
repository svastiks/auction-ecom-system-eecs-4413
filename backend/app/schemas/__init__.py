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
from app.schemas.order import (
    OrderResponse,
    OrderDetail,
    OrderCreate,
    PaymentRequest,
    PaymentResponse,
    PaymentResponseDetail,
    ReceiptResponse,
    ShipmentResponse,
    ShippingMethodUpdate,
    PayResponse,
    ShippingMethod,
    OrderStatus as OrderStatusEnum,
    PaymentStatus,
    ShipmentStatus,
)
from app.schemas.bid import MyBidItem, MyBidsResponse
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse, AddressListResponse
from app.schemas.auth import (
    UserSignUp, UserLogin, Token, PasswordForgot, PasswordReset, 
    PasswordResetConfirm, UserResponse as AuthUserResponse, AuthResponse, MessageResponse
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

# Import order schemas to rebuild forward refs
from app.schemas.order import OrderDetail, PaymentResponseDetail
OrderDetail.model_rebuild()
PaymentResponseDetail.model_rebuild()

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
    "OrderResponse",
    "OrderDetail",
    "OrderCreate",
    "PaymentRequest",
    "PaymentResponse",
    "PaymentResponseDetail",
    "ReceiptResponse",
    "ShipmentResponse",
    "ShippingMethodUpdate",
    "PayResponse",
    "ShippingMethod",
    "OrderStatusEnum",
    "PaymentStatus",
    "ShipmentStatus",
    # My Bids schemas
    "MyBidItem",
    "MyBidsResponse",
    # Address schemas
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
    "AddressListResponse",
    # Auth schemas
    "UserSignUp",
    "UserLogin",
    "Token",
    "PasswordForgot",
    "PasswordReset",
    "PasswordResetConfirm",
    "AuthUserResponse",
    "AuthResponse",
    "MessageResponse",
]