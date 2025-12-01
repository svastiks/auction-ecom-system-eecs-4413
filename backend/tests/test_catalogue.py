"""
Test suite for Catalogue endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal
from uuid import uuid4
import uuid

from app.models.catalogue import Category, CatalogueItem
from app.models.user import User
from app.core.security import get_password_hash


class TestCatalogueEndpoints:
    """Test catalogue management endpoints."""

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
    def seller_headers(self, seller):
        """Create auth headers for seller."""
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": str(seller.user_id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def category(self, db_session: Session):
        """Create a test category."""
        category = Category(
            category_id=uuid4(),
            name="Test Category",
            description="Test Description"
        )
        db_session.add(category)
        db_session.commit()
        return category

    # Category Tests
    def test_get_categories_empty(self, client: TestClient):
        """Test getting categories when none exist."""
        response = client.get("/api/v1/catalogue/categories")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_create_category_success(self, client: TestClient):
        """Test successful category creation."""
        category_data = {
            "name": "Electronics",
            "description": "Electronic items"
        }
        response = client.post("/api/v1/catalogue/categories", json=category_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Electronics"
        assert data["description"] == "Electronic items"

    def test_create_category_duplicate_name(self, client: TestClient, category):
        """Test creating category with duplicate name."""
        category_data = {
            "name": category.name,
            "description": "Another description"
        }
        response = client.post("/api/v1/catalogue/categories", json=category_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_get_category_by_id(self, client: TestClient, category):
        """Test getting category by ID."""
        response = client.get(f"/api/v1/catalogue/categories/{category.category_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == str(category.category_id)
        assert data["name"] == category.name

    def test_get_category_not_found(self, client: TestClient):
        """Test getting non-existent category."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/catalogue/categories/{fake_id}")
        
        assert response.status_code == 404

    def test_update_category_success(self, client: TestClient, category):
        """Test successful category update."""
        update_data = {
            "name": "Updated Category",
            "description": "Updated Description"
        }
        response = client.put(f"/api/v1/catalogue/categories/{category.category_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["description"] == "Updated Description"

    def test_delete_category_success(self, client: TestClient, db_session: Session):
        """Test successful category deletion."""
        category = Category(
            category_id=uuid4(),
            name="To Delete",
            description="Will be deleted"
        )
        db_session.add(category)
        db_session.commit()
        
        response = client.delete(f"/api/v1/catalogue/categories/{category.category_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

    def test_get_categories_with_pagination(self, client: TestClient, db_session: Session):
        """Test getting categories with pagination."""
        # Create multiple categories
        for i in range(5):
            category = Category(
                category_id=uuid4(),
                name=f"Category {i}",
                description=f"Description {i}"
            )
            db_session.add(category)
        db_session.commit()
        
        response = client.get("/api/v1/catalogue/categories?skip=0&limit=2")
        
        assert response.status_code == 200
        assert len(response.json()) == 2

    # Catalogue Item Tests
    def test_get_catalogue_items_empty(self, client: TestClient):
        """Test getting items when none exist."""
        response = client.get("/api/v1/catalogue/items")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_create_catalogue_item_success(self, client: TestClient, seller_headers, category):
        """Test successful item creation."""
        item_data = {
            "title": "Test Item",
            "description": "Test Description",
            "category_id": str(category.category_id),
            "base_price": "100.00",
            "shipping_price_normal": "10.00",
            "shipping_price_expedited": "25.00",
            "shipping_time_days": 5,
            "is_active": True
        }
        response = client.post("/api/v1/catalogue/items", json=item_data, headers=seller_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Item"
        assert data["base_price"] == "100.00"

    def test_create_item_without_auth(self, client: TestClient, category):
        """Test creating item without authentication."""
        item_data = {
            "title": "Test Item",
            "base_price": "100.00",
            "shipping_price_normal": "10.00",
            "shipping_price_expedited": "25.00",
            "shipping_time_days": 5
        }
        response = client.post("/api/v1/catalogue/items", json=item_data)
        
        assert response.status_code in [401, 403]  # FastAPI may return 403 for missing auth

    def test_get_catalogue_item_by_id(self, client: TestClient, db_session: Session, seller, category):
        """Test getting item by ID."""
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
        
        response = client.get(f"/api/v1/catalogue/items/{item.item_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == str(item.item_id)
        assert data["title"] == "Test Item"

    def test_get_catalogue_items_with_search(self, client: TestClient, db_session: Session, seller, category):
        """Test searching items."""
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
        db_session.commit()
        
        response = client.get("/api/v1/catalogue/items?search=laptop")
        
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1
        assert "laptop" in items[0]["title"].lower() or "laptop" in items[0]["description"].lower()

    def test_get_catalogue_items_with_category_filter(self, client: TestClient, db_session: Session, seller, category):
        """Test filtering items by category."""
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
        db_session.commit()
        
        response = client.get(f"/api/v1/catalogue/items?category_id={category.category_id}")
        
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1
        assert all(item["category_id"] == str(category.category_id) for item in items)

    def test_update_catalogue_item_success(self, client: TestClient, db_session: Session, seller, category):
        """Test successful item update."""
        item = CatalogueItem(
            item_id=uuid4(),
            seller_id=seller.user_id,
            title="Original Title",
            category_id=category.category_id,
            base_price=Decimal("100.00"),
            shipping_price_normal=Decimal("10.00"),
            shipping_price_expedited=Decimal("25.00"),
            shipping_time_days=5,
            is_active=True
        )
        db_session.add(item)
        db_session.commit()
        
        update_data = {
            "title": "Updated Title",
            "base_price": "150.00"
        }
        response = client.put(f"/api/v1/catalogue/items/{item.item_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["base_price"] == "150.00"

    def test_delete_catalogue_item_success(self, client: TestClient, db_session: Session, seller, category):
        """Test successful item deletion."""
        item = CatalogueItem(
            item_id=uuid4(),
            seller_id=seller.user_id,
            title="To Delete",
            category_id=category.category_id,
            base_price=Decimal("100.00"),
            shipping_price_normal=Decimal("10.00"),
            shipping_price_expedited=Decimal("25.00"),
            shipping_time_days=5,
            is_active=True
        )
        db_session.add(item)
        db_session.commit()
        
        response = client.delete(f"/api/v1/catalogue/items/{item.item_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

