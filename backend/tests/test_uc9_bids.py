import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models.user import User
from app.models.auction import Bid, Auction
from app.models.catalogue import CatalogueItem
from app.core.security import get_password_hash
import uuid

class TestUC9ViewMyBids:
    """Test UC9: View My Bids functionality."""

    def test_get_my_bids_empty(self, client: TestClient, auth_headers):
        """Test getting bids when user has no bids (Alternate A1)."""
        response = client.get("/api/v1/users/me/bids", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["bids"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_get_my_bids_with_leading_bid(self, client: TestClient, auth_headers, db_session: Session, test_user):
        """Test getting bids where user has the leading bid."""
        # Create an item and auction
        item = CatalogueItem(
            item_id=uuid.uuid4(),
            seller_id=test_user.user_id,
            title="Test Item",
            base_price=Decimal("10.00"),
            shipping_price_normal=Decimal("5.00"),
            shipping_price_expedited=Decimal("10.00"),
            shipping_time_days=3,
            is_active=True
        )
        db_session.add(item)
        db_session.commit()
        
        auction = Auction(
            auction_id=uuid.uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("10.00"),
            min_increment=Decimal("1.00"),
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            status="ACTIVE"
        )
        db_session.add(auction)
        db_session.commit()
        
        # Create a bid from the user
        bid = Bid(
            bid_id=uuid.uuid4(),
            auction_id=auction.auction_id,
            bidder_id=test_user.user_id,
            amount=Decimal("50.00")
        )
        db_session.add(bid)
        db_session.commit()
        
        response = client.get("/api/v1/users/me/bids", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["bids"]) == 1
        assert data["bids"][0]["status"] == "LEADING"
        assert data["bids"][0]["item_title"] == "Test Item"
        assert float(data["bids"][0]["last_bid_amount"]) == 50.0
        assert data["bids"][0]["time_left_seconds"] is not None

    def test_get_my_bids_with_outbid_status(self, client: TestClient, auth_headers, db_session: Session, test_user):
        """Test getting bids where user has been outbid."""
        # Create another user
        other_user = User(
            user_id=uuid.uuid4(),
            username="otheruser",
            email="other@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Other",
            last_name="User",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        # Create item and auction
        item = CatalogueItem(
            item_id=uuid.uuid4(),
            seller_id=other_user.user_id,
            title="Auctioned Item",
            base_price=Decimal("10.00"),
            shipping_price_normal=Decimal("5.00"),
            shipping_price_expedited=Decimal("10.00"),
            shipping_time_days=3,
            is_active=True
        )
        db_session.add(item)
        db_session.commit()
        
        auction = Auction(
            auction_id=uuid.uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("10.00"),
            min_increment=Decimal("1.00"),
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            status="ACTIVE"
        )
        db_session.add(auction)
        db_session.commit()
        
        # User places bid
        user_bid = Bid(
            bid_id=uuid.uuid4(),
            auction_id=auction.auction_id,
            bidder_id=test_user.user_id,
            amount=Decimal("30.00")
        )
        db_session.add(user_bid)
        
        # Other user outbids
        other_bid = Bid(
            bid_id=uuid.uuid4(),
            auction_id=auction.auction_id,
            bidder_id=other_user.user_id,
            amount=Decimal("50.00")
        )
        db_session.add(other_bid)
        db_session.commit()
        
        response = client.get("/api/v1/users/me/bids", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["bids"][0]["status"] == "OUTBID"
        assert float(data["bids"][0]["current_highest_bid"]) == 50.0

    def test_get_my_bids_ended_auction(self, client: TestClient, auth_headers, db_session: Session, test_user):
        """Test getting bids for ended auction (Alternate A2)."""
        # Create item and ended auction
        item = CatalogueItem(
            item_id=uuid.uuid4(),
            seller_id=test_user.user_id,
            title="Ended Item",
            base_price=Decimal("10.00"),
            shipping_price_normal=Decimal("5.00"),
            shipping_price_expedited=Decimal("10.00"),
            shipping_time_days=3,
            is_active=True
        )
        db_session.add(item)
        db_session.commit()
        
        auction = Auction(
            auction_id=uuid.uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("10.00"),
            min_increment=Decimal("1.00"),
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status="ENDED",
            winning_bidder_id=test_user.user_id
        )
        db_session.add(auction)
        db_session.commit()
        
        bid = Bid(
            bid_id=uuid.uuid4(),
            auction_id=auction.auction_id,
            bidder_id=test_user.user_id,
            amount=Decimal("100.00")
        )
        db_session.add(bid)
        db_session.commit()
        
        response = client.get("/api/v1/users/me/bids", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["bids"][0]["status"] in ["ENDED", "WON"]
        assert data["bids"][0]["time_left_seconds"] is None
        assert data["bids"][0]["auction_status"] == "ENDED"

    def test_get_my_bids_pagination(self, client: TestClient, auth_headers, db_session: Session, test_user):
        """Test pagination for user bids."""
        # Create multiple auctions and bids
        for i in range(5):
            item = CatalogueItem(
                item_id=uuid.uuid4(),
                seller_id=test_user.user_id,
                title=f"Item {i}",
                base_price=Decimal("10.00"),
                shipping_price_normal=Decimal("5.00"),
                shipping_price_expedited=Decimal("10.00"),
                shipping_time_days=3,
                is_active=True
            )
            db_session.add(item)
            db_session.flush()
            
            auction = Auction(
                auction_id=uuid.uuid4(),
                item_id=item.item_id,
                auction_type="FORWARD",
                starting_price=Decimal("10.00"),
                min_increment=Decimal("1.00"),
                start_time=datetime.now(timezone.utc) - timedelta(hours=1),
                end_time=datetime.now(timezone.utc) + timedelta(hours=1),
                status="ACTIVE"
            )
            db_session.add(auction)
            db_session.flush()
            
            bid = Bid(
                bid_id=uuid.uuid4(),
                auction_id=auction.auction_id,
                bidder_id=test_user.user_id,
                amount=Decimal(f"{20 + i}.00")
            )
            db_session.add(bid)
        
        db_session.commit()
        
        # Get first page
        response = client.get("/api/v1/users/me/bids?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["bids"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    def test_get_my_bids_unauthenticated(self, client: TestClient):
        """Test that unauthenticated users cannot access bids."""
        response = client.get("/api/v1/users/me/bids")
        
        assert response.status_code in [401, 403]  # FastAPI may return 403 for missing auth
