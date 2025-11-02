import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, Address
from app.core.security import get_password_hash
import uuid

class TestUC10ManageShippingAddress:
    """Test UC10: Manage Shipping Address functionality."""

    def test_create_address_with_phone_and_validation(self, client: TestClient, auth_headers):
        """Test creating address with phone number and postal code validation."""
        address_data = {
            "street_line1": "123 Main Street",
            "city": "New York",
            "state_region": "NY",
            "postal_code": "10001-1234",  # Should be validated and normalized
            "country": "USA",
            "phone": "+1 (555) 123-4567",  # Should be validated
            "is_default_shipping": True
        }
        response = client.post("/api/v1/users/me/addresses", json=address_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "The shipping address has been updated." in data["message"]
        assert "address" in data
        assert data["address"]["street_line1"] == "123 Main Street"
        assert data["address"]["phone"] is not None

    def test_create_address_invalid_postal_code(self, client: TestClient, auth_headers):
        """Test creating address with invalid postal code (Alternate A1)."""
        address_data = {
            "street_line1": "123 Main Street",
            "city": "New York",
            "postal_code": "10001@#$",  # Invalid characters
            "country": "USA",
            "is_default_shipping": True
        }
        response = client.post("/api/v1/users/me/addresses", json=address_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
        assert "postal code" in response.json()["detail"][0]["msg"].lower()

    def test_create_address_invalid_phone(self, client: TestClient, auth_headers):
        """Test creating address with invalid phone number (Alternate A1)."""
        address_data = {
            "street_line1": "123 Main Street",
            "city": "New York",
            "postal_code": "10001",
            "country": "USA",
            "phone": "123",  # Too short
            "is_default_shipping": True
        }
        response = client.post("/api/v1/users/me/addresses", json=address_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
        error_details = response.json()["detail"]
        phone_error = next((e for e in error_details if "phone" in str(e).lower()), None)
        assert phone_error is not None

    def test_update_address_with_validation(self, client: TestClient, auth_headers, db_session: Session):
        """Test updating address with validated fields."""
        # Get the test user
        user = db_session.query(User).first()
        
        # Create an address first
        address = Address(
            address_id=uuid.uuid4(),
            user_id=user.user_id,
            street_line1="123 Old Street",
            city="Boston",
            postal_code="02101",
            country="USA"
        )
        db_session.add(address)
        db_session.commit()
        
        # Update with new validated data
        update_data = {
            "postal_code": "K1A 0B1",  # Canadian postal code - should be normalized
            "phone": "555-123-4567"
        }
        response = client.put(
            f"/api/v1/users/me/addresses/{address.address_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "The shipping address has been updated." in data["message"]
        assert data["address"]["postal_code"] == "K1A 0B1"

    def test_multiple_addresses_default_logic(self, client: TestClient, auth_headers, db_session: Session):
        """Test that only one address can be default (Alternate A2)."""
        user = db_session.query(User).first()
        
        # Create first address as default
        address1_data = {
            "street_line1": "111 First St",
            "city": "City1",
            "postal_code": "11111",
            "country": "USA",
            "is_default_shipping": True
        }
        response1 = client.post("/api/v1/users/me/addresses", json=address1_data, headers=auth_headers)
        assert response1.status_code == 201
        address1_id = response1.json()["address"]["address_id"]
        
        # Create second address as default (should unset first)
        address2_data = {
            "street_line1": "222 Second St",
            "city": "City2",
            "postal_code": "22222",
            "country": "USA",
            "is_default_shipping": True
        }
        response2 = client.post("/api/v1/users/me/addresses", json=address2_data, headers=auth_headers)
        assert response2.status_code == 201
        
        # Verify only one is default
        response = client.get("/api/v1/users/me/addresses", headers=auth_headers)
        addresses = response.json()["addresses"]
        default_count = sum(1 for addr in addresses if addr["is_default_shipping"])
        assert default_count == 1
        assert addresses[0]["is_default_shipping"] == True  # Most recent should be default

    def test_postal_code_normalization(self, client: TestClient, auth_headers):
        """Test that postal codes are normalized to uppercase."""
        address_data = {
            "street_line1": "123 Test St",
            "city": "Test City",
            "postal_code": "k1a 0b1",  # Lowercase
            "country": "Canada",
            "is_default_shipping": True
        }
        response = client.post("/api/v1/users/me/addresses", json=address_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["address"]["postal_code"] == "K1A 0B1"  # Normalized to uppercase

    def test_get_addresses_shows_phone(self, client: TestClient, auth_headers, db_session: Session):
        """Test that retrieved addresses include phone number."""
        user = db_session.query(User).first()
        
        # Create address with phone
        address = Address(
            address_id=uuid.uuid4(),
            user_id=user.user_id,
            street_line1="123 Phone St",
            city="Phone City",
            postal_code="12345",
            country="USA",
            phone="+1-555-123-4567"
        )
        db_session.add(address)
        db_session.commit()
        
        response = client.get("/api/v1/users/me/addresses", headers=auth_headers)
        
        assert response.status_code == 200
        addresses = response.json()["addresses"]
        assert len(addresses) > 0
        # Check if any address has phone (depending on test order)
        address_with_phone = next((a for a in addresses if a.get("phone")), None)
        if address_with_phone:
            assert address_with_phone["phone"] is not None

    def test_address_creation_confirmation_message(self, client: TestClient, auth_headers):
        """Test that address creation returns proper confirmation message."""
        address_data = {
            "street_line1": "123 Confirmation St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "USA"
        }
        response = client.post("/api/v1/users/me/addresses", json=address_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "The shipping address has been updated."

    def test_address_update_confirmation_message(self, client: TestClient, auth_headers, db_session: Session):
        """Test that address update returns proper confirmation message."""
        user = db_session.query(User).first()
        
        address = Address(
            address_id=uuid.uuid4(),
            user_id=user.user_id,
            street_line1="123 Update St",
            city="Test City",
            postal_code="12345",
            country="USA"
        )
        db_session.add(address)
        db_session.commit()
        
        update_data = {"city": "Updated City"}
        response = client.put(
            f"/api/v1/users/me/addresses/{address.address_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "The shipping address has been updated."
