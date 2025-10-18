import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, Address

class TestUserEndpoints:
    """Test user management endpoints."""

    def test_get_current_user_profile(self, client: TestClient, auth_headers, test_user):
        """Test getting current user profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user.user_id)
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_update_user_profile_success(self, client: TestClient, auth_headers, test_user):
        """Test successful profile update."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+9876543210"
        }
        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["phone"] == "+9876543210"

    def test_update_user_profile_duplicate_email(self, client: TestClient, auth_headers, db_session: Session):
        """Test profile update with duplicate email."""
        # Create another user
        from app.core.security import get_password_hash
        import uuid
        
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
        
        update_data = {"email": "other@example.com"}
        response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_get_user_addresses_empty(self, client: TestClient, auth_headers):
        """Test getting addresses when user has none."""
        response = client.get("/api/v1/users/me/addresses", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["addresses"] == []
        assert data["total"] == 0

    def test_create_address_success(self, client: TestClient, auth_headers):
        """Test successful address creation."""
        address_data = {
            "street_line1": "123 Main St",
            "street_line2": "Apt 4B",
            "city": "New York",
            "state_region": "NY",
            "postal_code": "10001",
            "country": "USA",
            "is_default_shipping": True
        }
        response = client.post("/api/v1/users/me/addresses", json=address_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["street_line1"] == "123 Main St"
        assert data["city"] == "New York"
        assert data["is_default_shipping"] == True

    def test_create_multiple_addresses_default_logic(self, client: TestClient, auth_headers):
        """Test that only one address can be default."""
        # Create first address as default
        address1_data = {
            "street_line1": "123 Main St",
            "city": "New York",
            "postal_code": "10001",
            "country": "USA",
            "is_default_shipping": True
        }
        response1 = client.post("/api/v1/users/me/addresses", json=address1_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Create second address as default (should unset first)
        address2_data = {
            "street_line1": "456 Oak Ave",
            "city": "Boston",
            "postal_code": "02101",
            "country": "USA",
            "is_default_shipping": True
        }
        response2 = client.post("/api/v1/users/me/addresses", json=address2_data, headers=auth_headers)
        assert response2.status_code == 201
        
        # Check that only the second address is default
        response = client.get("/api/v1/users/me/addresses", headers=auth_headers)
        addresses = response.json()["addresses"]
        default_count = sum(1 for addr in addresses if addr["is_default_shipping"])
        assert default_count == 1
        assert addresses[0]["is_default_shipping"] == True  # Most recent should be default

    def test_update_address_success(self, client: TestClient, auth_headers, db_session: Session):
        """Test successful address update."""
        # Create an address first
        from app.core.security import get_password_hash
        import uuid
        
        user = db_session.query(User).first()
        address = Address(
            address_id=uuid.uuid4(),
            user_id=user.user_id,
            street_line1="123 Main St",
            city="New York",
            postal_code="10001",
            country="USA",
            is_default_shipping=True
        )
        db_session.add(address)
        db_session.commit()
        
        update_data = {
            "street_line1": "456 Updated St",
            "city": "Boston"
        }
        response = client.put(f"/api/v1/users/me/addresses/{address.address_id}", 
                             json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["street_line1"] == "456 Updated St"
        assert data["city"] == "Boston"

    def test_delete_address_success(self, client: TestClient, auth_headers, db_session: Session):
        """Test successful address deletion."""
        # Create an address first
        from app.core.security import get_password_hash
        import uuid
        
        user = db_session.query(User).first()
        address = Address(
            address_id=uuid.uuid4(),
            user_id=user.user_id,
            street_line1="123 Main St",
            city="New York",
            postal_code="10001",
            country="USA"
        )
        db_session.add(address)
        db_session.commit()
        
        response = client.delete(f"/api/v1/users/me/addresses/{address.address_id}", 
                                headers=auth_headers)
        
        assert response.status_code == 200
        assert "Address deleted successfully" in response.json()["message"]

    def test_access_other_user_address(self, client: TestClient, auth_headers, db_session: Session):
        """Test that users cannot access other users' addresses."""
        # Create another user and address
        from app.core.security import get_password_hash
        import uuid
        
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
        
        other_address = Address(
            address_id=uuid.uuid4(),
            user_id=other_user.user_id,
            street_line1="999 Other St",
            city="Other City",
            postal_code="99999",
            country="Other Country"
        )
        db_session.add(other_address)
        db_session.commit()
        
        # Try to access other user's address
        response = client.put(f"/api/v1/users/me/addresses/{other_address.address_id}", 
                            json={"city": "Hacked"}, headers=auth_headers)
        
        assert response.status_code == 404
        assert "Address not found" in response.json()["detail"]
