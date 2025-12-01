"""
Test suite for Auction endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import uuid

from app.models.user import User
from app.models.catalogue import Category, CatalogueItem
from app.models.auction import Auction, Bid
from app.schemas.auction import AuctionStatus
from app.core.security import get_password_hash


class TestAuctionEndpoints:
    """Test auction management endpoints."""

    @pytest.fixture
    def seller(self, db_session: Session):
        """Create a seller user."""
        seller = User(
            user_id=uuid4(),
            username="seller",
            email="seller@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Seller",
            last_name="User",
            is_active=True
        )
        db_session.add(seller)
        db_session.commit()
        return seller

    @pytest.fixture
    def buyer(self, db_session: Session):
        """Create a buyer user."""
        buyer = User(
            user_id=uuid4(),
            username="buyer",
            email="buyer@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Buyer",
            last_name="User",
            is_active=True
        )
        db_session.add(buyer)
        db_session.commit()
        return buyer

    @pytest.fixture
    def seller_headers(self, seller):
        """Create auth headers for seller."""
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(seller.user_id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def buyer_headers(self, buyer):
        """Create auth headers for buyer."""
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(buyer.user_id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def category(self, db_session: Session):
        """Create a test category."""
        category = Category(
            category_id=uuid4(),
            name="Electronics",
            description="Electronic items"
        )
        db_session.add(category)
        db_session.commit()
        return category

    @pytest.fixture
    def item(self, db_session: Session, seller, category):
        """Create a test catalogue item."""
        item = CatalogueItem(
            item_id=uuid4(),
            seller_id=seller.user_id,
            title="Laptop Computer",
            description="A great laptop for sale",
            category_id=category.category_id,
            base_price=Decimal("999.99"),
            shipping_price_normal=Decimal("10.00"),
            shipping_price_expedited=Decimal("25.00"),
            shipping_time_days=5,
            is_active=True
        )
        db_session.add(item)
        db_session.commit()
        return item

    def test_create_auction_success(self, client: TestClient, seller_headers, item):
        """Test successful auction creation."""
        now = datetime.now(timezone.utc)
        auction_data = {
            "item_id": str(item.item_id),
            "auction_type": "FORWARD",
            "starting_price": "1000.00",
            "min_increment": "50.00",
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(days=7)).isoformat(),
            "status": "SCHEDULED"
        }
        response = client.post("/api/v1/auction", json=auction_data, headers=seller_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["starting_price"] == "1000.00"
        assert data["status"] in ["SCHEDULED", "ACTIVE"]

    def test_create_auction_not_seller(self, client: TestClient, buyer_headers, item):
        """Test that only seller can create auction."""
        now = datetime.now(timezone.utc)
        auction_data = {
            "item_id": str(item.item_id),
            "auction_type": "FORWARD",
            "starting_price": "1000.00",
            "min_increment": "50.00",
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(days=7)).isoformat()
        }
        response = client.post("/api/v1/auction", json=auction_data, headers=buyer_headers)
        
        assert response.status_code == 403

    def test_create_auction_without_auth(self, client: TestClient, item):
        """Test creating auction without authentication."""
        now = datetime.now(timezone.utc)
        auction_data = {
            "item_id": str(item.item_id),
            "auction_type": "FORWARD",
            "starting_price": "1000.00",
            "min_increment": "50.00",
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(days=7)).isoformat()
        }
        response = client.post("/api/v1/auction", json=auction_data)
        
        assert response.status_code in [401, 403]  # FastAPI may return 403 for missing auth

    def test_search_auctions_empty(self, client: TestClient):
        """Test searching auctions when none exist."""
        search_data = {
            "keyword": "laptop",
            "skip": 0,
            "limit": 20
        }
        response = client.post("/api/v1/auction/search", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["items"] == []

    def test_search_auctions_by_keyword(self, client: TestClient, db_session: Session, seller, category):
        """Test searching auctions by keyword."""
        # Create item and auction
        item = CatalogueItem(
            item_id=uuid4(),
            seller_id=seller.user_id,
            title="Laptop Computer",
            description="A great laptop",
            category_id=category.category_id,
            base_price=Decimal("999.99"),
            shipping_price_normal=Decimal("10.00"),
            shipping_price_expedited=Decimal("25.00"),
            shipping_time_days=5,
            is_active=True
        )
        db_session.add(item)
        db_session.flush()
        
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("1000.00"),
            min_increment=Decimal("50.00"),
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=7),
            status=AuctionStatus.ACTIVE.value
        )
        db_session.add(auction)
        db_session.commit()
        
        search_data = {
            "keyword": "laptop",
            "skip": 0,
            "limit": 20
        }
        response = client.post("/api/v1/auction/search", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1
        assert any("laptop" in item["title"].lower() for item in data["items"])

    def test_get_auction_item_detail(self, client: TestClient, db_session: Session, seller, category):
        """Test getting auction item detail."""
        item = CatalogueItem(
            item_id=uuid4(),
            seller_id=seller.user_id,
            title="Test Item",
            category_id=category.category_id,
            base_price=Decimal("100.00"),
            shipping_price_normal=Decimal("10.00"),
            shipping_price_expedited=Decimal("25.00"),
            shipping_time_days=5,
            is_active=True
        )
        db_session.add(item)
        db_session.flush()
        
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("100.00"),
            min_increment=Decimal("10.00"),
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=7),
            status=AuctionStatus.ACTIVE.value
        )
        db_session.add(auction)
        db_session.commit()
        
        response = client.get(f"/api/v1/auction/items/{item.item_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == str(item.item_id)
        assert data["title"] == "Test Item"

    def test_get_auction_by_id(self, client: TestClient, db_session: Session, seller, item):
        """Test getting auction by ID."""
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("1000.00"),
            min_increment=Decimal("50.00"),
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=7),
            status=AuctionStatus.ACTIVE.value
        )
        db_session.add(auction)
        db_session.commit()
        
        response = client.get(f"/api/v1/auction/{auction.auction_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["auction_id"] == str(auction.auction_id)
        assert data["starting_price"] == "1000.00"

    def test_place_bid_success(self, client: TestClient, db_session: Session, seller, buyer, item, buyer_headers):
        """Test successful bid placement."""
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("1000.00"),
            min_increment=Decimal("50.00"),
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=7),
            status=AuctionStatus.ACTIVE.value
        )
        db_session.add(auction)
        db_session.commit()
        
        bid_data = {
            "auction_id": str(auction.auction_id),
            "amount": "1050.00"
        }
        response = client.post("/api/v1/auction/bid", json=bid_data, headers=buyer_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "1050.00"

    def test_place_bid_below_minimum(self, client: TestClient, db_session: Session, seller, buyer, item, buyer_headers):
        """Test bid below minimum increment."""
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("1000.00"),
            min_increment=Decimal("50.00"),
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=7),
            status=AuctionStatus.ACTIVE.value
        )
        db_session.add(auction)
        db_session.commit()
        
        bid_data = {
            "auction_id": str(auction.auction_id),
            "amount": "1020.00"  # Below minimum increment
        }
        response = client.post("/api/v1/auction/bid", json=bid_data, headers=buyer_headers)
        
        assert response.status_code in [400, 422]

    def test_place_bid_on_ended_auction(self, client: TestClient, db_session: Session, seller, buyer, item, buyer_headers):
        """Test bid on ended auction."""
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("1000.00"),
            min_increment=Decimal("50.00"),
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(hours=1),
            status=AuctionStatus.ENDED.value
        )
        db_session.add(auction)
        db_session.commit()
        
        bid_data = {
            "auction_id": str(auction.auction_id),
            "amount": "1050.00"
        }
        response = client.post("/api/v1/auction/bid", json=bid_data, headers=buyer_headers)
        
        assert response.status_code == 400
        assert "ended" in response.json()["detail"].lower()

    def test_get_auction_bids(self, client: TestClient, db_session: Session, seller, buyer, item):
        """Test getting bids for an auction."""
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("1000.00"),
            min_increment=Decimal("50.00"),
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(days=7),
            status=AuctionStatus.ACTIVE.value
        )
        db_session.add(auction)
        db_session.flush()
        
        bid = Bid(
            bid_id=uuid4(),
            auction_id=auction.auction_id,
            bidder_id=buyer.user_id,
            amount=Decimal("1050.00")
        )
        db_session.add(bid)
        db_session.commit()
        
        response = client.get(f"/api/v1/auction/{auction.auction_id}/bids")
        
        assert response.status_code == 200
        bids = response.json()
        assert len(bids) >= 1
        assert bids[0]["amount"] == "1050.00"

    def test_get_auction_not_found(self, client: TestClient):
        """Test getting non-existent auction."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/auction/{fake_id}")
        
        assert response.status_code == 404

