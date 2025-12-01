import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
import uuid

# Test database URL (using SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Import all models except EventLog (SQLite doesn't support JSONB)
    from app.models.user import User, Address, AuthSession, PasswordResetToken
    from app.models.catalogue import Category, CatalogueItem, ItemImage
    from app.models.auction import Auction, Bid
    from app.models.order import Order, Payment, Receipt, Shipment
    
    # Create only the tables we need (excluding EventLog)
    tables_to_create = [
        User.__table__,
        Address.__table__,
        AuthSession.__table__,
        PasswordResetToken.__table__,
        Category.__table__,
        CatalogueItem.__table__,
        ItemImage.__table__,
        Auction.__table__,
        Bid.__table__,
        Order.__table__,
        Payment.__table__,
        Receipt.__table__,
        Shipment.__table__,
    ]
    
    Base.metadata.create_all(bind=engine, tables=tables_to_create)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine, tables=tables_to_create)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+1234567890"
    }

@pytest.fixture
def test_user(db_session, test_user_data):
    """Create a test user in the database."""
    from app.core.security import get_password_hash
    from app.models.user import User
    
    user = User(
        user_id=uuid.uuid4(),
        username=test_user_data["username"],
        email=test_user_data["email"],
        password_hash=get_password_hash(test_user_data["password"]),
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        phone=test_user_data["phone"],
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    token = create_access_token(data={"sub": str(test_user.user_id)})
    return {"Authorization": f"Bearer {token}"}
