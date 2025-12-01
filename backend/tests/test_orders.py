"""
Test suite for UC4/UC5/UC6: Pay Now, payment capture, receipt and shipment.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import uuid

from app.models.user import User, Address
from app.models.catalogue import CatalogueItem, Category
from app.models.auction import Auction, Bid
from app.models.order import Order, Payment, Receipt, Shipment
from app.schemas.auction import AuctionStatus


class TestOrderEndpoints:
    """Test order management endpoints."""

    @pytest.fixture
    def seller(self, db_session: Session):
        """Create a seller user."""
        from app.core.security import get_password_hash
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
        """Create a buyer user (winning bidder)."""
        from app.core.security import get_password_hash
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
    def other_user(self, db_session: Session):
        """Create another user (non-winning bidder)."""
        from app.core.security import get_password_hash
        other = User(
            user_id=uuid4(),
            username="other",
            email="other@example.com",
            password_hash=get_password_hash("password123"),
            first_name="Other",
            last_name="User",
            is_active=True
        )
        db_session.add(other)
        db_session.commit()
        return other

    @pytest.fixture
    def category(self, db_session: Session):
        """Create a category."""
        category = Category(
            category_id=uuid4(),
            name="Test Category",
            description="Test Description"
        )
        db_session.add(category)
        db_session.commit()
        return category

    @pytest.fixture
    def item(self, db_session: Session, seller, category):
        """Create a catalogue item."""
        item = CatalogueItem(
            item_id=uuid4(),
            seller_id=seller.user_id,
            title="Test Item",
            description="Test Description",
            category_id=category.category_id,
            base_price=Decimal("100.00"),
            shipping_price_normal=Decimal("10.00"),
            shipping_price_expedited=Decimal("25.00"),
            shipping_time_days=5,
            is_active=True
        )
        db_session.add(item)
        db_session.commit()
        return item

    @pytest.fixture
    def ended_auction(self, db_session: Session, item, buyer):
        """Create an ended auction with a winning bid."""
        now = datetime.now(timezone.utc)
        auction = Auction(
            auction_id=uuid4(),
            item_id=item.item_id,
            auction_type="FORWARD",
            starting_price=Decimal("100.00"),
            min_increment=Decimal("5.00"),
            start_time=now - timedelta(days=1),
            end_time=now - timedelta(hours=1),
            status=AuctionStatus.ENDED.value,
            winning_bidder_id=buyer.user_id
        )
        db_session.add(auction)
        db_session.flush()
        
        # Create winning bid
        winning_bid = Bid(
            bid_id=uuid4(),
            auction_id=auction.auction_id,
            bidder_id=buyer.user_id,
            amount=Decimal("150.00")
        )
        auction.winning_bid_id = winning_bid.bid_id
        db_session.add(winning_bid)
        db_session.commit()
        db_session.refresh(auction)
        return auction

    @pytest.fixture
    def shipping_address(self, db_session: Session, buyer):
        """Create a shipping address for buyer."""
        address = Address(
            address_id=uuid4(),
            user_id=buyer.user_id,
            street_line1="123 Main St",
            city="New York",
            postal_code="10001",
            country="USA",
            is_default_shipping=True
        )
        db_session.add(address)
        db_session.commit()
        return address

    @pytest.fixture
    def order(self, db_session: Session, ended_auction, buyer, shipping_address):
        """Create an order in PENDING_PAYMENT status."""
        order = Order(
            order_id=uuid4(),
            auction_id=ended_auction.auction_id,
            buyer_id=buyer.user_id,
            item_id=ended_auction.item_id,
            winning_bid_amount=Decimal("150.00"),
            shipping_method="NORMAL",
            shipping_cost=Decimal("10.00"),
            total_amount=Decimal("160.00"),
            shipping_address_id=shipping_address.address_id,
            status="PENDING_PAYMENT"
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        return order

    @pytest.fixture
    def buyer_headers(self, buyer):
        """Create auth headers for buyer."""
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(buyer.user_id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def seller_headers(self, seller):
        """Create auth headers for seller."""
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(seller.user_id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def other_headers(self, other_user):
        """Create auth headers for other user."""
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(other_user.user_id)})
        return {"Authorization": f"Bearer {token}"}

    def test_create_order_success(self, client: TestClient, buyer_headers, ended_auction, shipping_address):
        """Test 1: Create order successfully."""
        order_data = {
            "auction_id": str(ended_auction.auction_id),
            "shipping_method": "NORMAL",
            "shipping_address_id": str(shipping_address.address_id)
        }
        response = client.post("/api/v1/orders", json=order_data, headers=buyer_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PENDING_PAYMENT"
        assert data["shipping_method"] == "NORMAL"
        assert float(data["total_amount"]) == 160.00  # 150.00 bid + 10.00 shipping

    def test_pay_order_success(self, client: TestClient, buyer_headers, order):
        """Test 2: Pay order successfully."""
        payment_data = {
            "card_number": "4111111111111111",
            "card_holder_name": "Buyer User",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
        response = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=buyer_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CAPTURED"
        assert data["message"] == "Payment processed successfully"
        
        # Verify order status
        order_response = client.get(f"/api/v1/orders/{order.order_id}", headers=buyer_headers)
        assert order_response.status_code == 200
        order_data = order_response.json()
        assert order_data["status"] == "PAID"
        
        # Verify receipt was created
        receipt_response = client.get(f"/api/v1/orders/{order.order_id}/receipt", headers=buyer_headers)
        assert receipt_response.status_code == 200
        receipt_data = receipt_response.json()
        assert receipt_data["total_paid"] == "160.00"
        
        # Verify shipment was created
        shipment_response = client.get(f"/api/v1/orders/{order.order_id}/shipment", headers=buyer_headers)
        assert shipment_response.status_code == 200
        shipment_data = shipment_response.json()
        assert shipment_data["status"] == "PENDING"
        assert shipment_data["estimated_days"] == 5

    def test_pay_order_non_winner(self, client: TestClient, other_headers, order):
        """Test 3: Non-winning bidder cannot pay (403/409)."""
        payment_data = {
            "card_number": "4111111111111111",
            "card_holder_name": "Other User",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
        response = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=other_headers
        )
        
        assert response.status_code in [403, 409]
        assert "winning bidder" in response.json()["detail"].lower()

    def test_pay_order_duplicate_idempotency(self, client: TestClient, buyer_headers, order):
        """Test 4: Duplicate payment is idempotent."""
        payment_data = {
            "card_number": "4111111111111111",
            "card_holder_name": "Buyer User",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
        
        # First payment
        response1 = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=buyer_headers
        )
        assert response1.status_code == 200
        payment_id_1 = response1.json()["payment_id"]
        
        # Second payment attempt (idempotent)
        response2 = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=buyer_headers
        )
        assert response2.status_code == 200
        assert response2.json()["payment_id"] == payment_id_1
        assert "already processed" in response2.json()["message"].lower()

    def test_pay_order_failure_case(self, client: TestClient, buyer_headers, order):
        """Test 5: Payment failure with card number starting with 4000."""
        payment_data = {
            "card_number": "4000123456789012",
            "card_holder_name": "Buyer User",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
        response = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=buyer_headers
        )
        
        assert response.status_code == 402
        detail = response.json()["detail"].lower()
        assert any(word in detail for word in ["failed", "declined", "card"])
        
        # Verify order status is FAILED
        order_response = client.get(f"/api/v1/orders/{order.order_id}", headers=buyer_headers)
        assert order_response.status_code == 200
        order_data = order_response.json()
        assert order_data["status"] == "FAILED"
        
        # Verify payment status is FAILED
        assert order_data["payment"]["status"] == "FAILED"

    def test_update_shipping_method_normal_to_expedited(self, client: TestClient, buyer_headers, order):
        """Test 6: Update shipping method from NORMAL to EXPEDITED and verify totals."""
        # Get initial order
        initial_response = client.get(f"/api/v1/orders/{order.order_id}", headers=buyer_headers)
        initial_total = float(initial_response.json()["total_amount"])
        assert initial_total == 160.00  # 150.00 + 10.00
        
        # Update to expedited
        update_data = {"shipping_method": "EXPEDITED"}
        response = client.put(
            f"/api/v1/orders/{order.order_id}/shipping-method",
            json=update_data,
            headers=buyer_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["shipping_method"] == "EXPEDITED"
        assert float(data["shipping_cost"]) == 25.00
        assert float(data["total_amount"]) == 175.00  # 150.00 + 25.00

    def test_get_receipt_after_payment(self, client: TestClient, buyer_headers, order):
        """Test 7: Get receipt after successful payment."""
        # Pay first
        payment_data = {
            "card_number": "4111111111111111",
            "card_holder_name": "Buyer User",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
        pay_response = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=buyer_headers
        )
        assert pay_response.status_code == 200
        
        # Get receipt
        receipt_response = client.get(f"/api/v1/orders/{order.order_id}/receipt", headers=buyer_headers)
        assert receipt_response.status_code == 200
        receipt_data = receipt_response.json()
        assert "receipt_number" in receipt_data
        assert receipt_data["total_paid"] == "160.00"
        assert receipt_data["issued_at"] is not None

    def test_get_shipment_after_payment(self, client: TestClient, buyer_headers, order):
        """Test 8: Get shipment after successful payment."""
        # Pay first
        payment_data = {
            "card_number": "4111111111111111",
            "card_holder_name": "Buyer User",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
        pay_response = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=buyer_headers
        )
        assert pay_response.status_code == 200
        
        # Get shipment
        shipment_response = client.get(f"/api/v1/orders/{order.order_id}/shipment", headers=buyer_headers)
        assert shipment_response.status_code == 200
        shipment_data = shipment_response.json()
        assert shipment_data["status"] == "PENDING"
        assert shipment_data["estimated_days"] == 5
        assert shipment_data["order_id"] == str(order.order_id)

    def test_update_shipping_method_recalculates_total(self, client: TestClient, buyer_headers, order):
        """Test 9: Verify total calculation includes shipping cost correctly."""
        # Update shipping method and verify total
        update_data = {"shipping_method": "EXPEDITED"}
        response = client.put(
            f"/api/v1/orders/{order.order_id}/shipping-method",
            json=update_data,
            headers=buyer_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        winning_bid = float(data["winning_bid_amount"])
        shipping_cost = float(data["shipping_cost"])
        total = float(data["total_amount"])
        
        # Verify: total_amount = winning_bid_amount + shipping_cost
        assert total == winning_bid + shipping_cost
        assert total == 175.00  # 150.00 + 25.00

    def test_cannot_pay_already_paid_order(self, client: TestClient, buyer_headers, order, db_session: Session):
        """Test 10: Cannot pay an already paid order (except for idempotency)."""
        # Mark order as paid
        order.status = "PAID"
        payment = Payment(
            payment_id=uuid4(),
            order_id=order.order_id,
            amount=order.total_amount,
            currency="USD",
            status="CAPTURED",
            processor="DUMMY"
        )
        db_session.add(payment)
        db_session.commit()
        
        # Try to pay again
        payment_data = {
            "card_number": "4111111111111111",
            "card_holder_name": "Buyer User",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
        response = client.post(
            f"/api/v1/orders/{order.order_id}/pay",
            json=payment_data,
            headers=buyer_headers
        )
        
        # Should return idempotent success
        assert response.status_code == 200
        assert "already processed" in response.json()["message"].lower()

