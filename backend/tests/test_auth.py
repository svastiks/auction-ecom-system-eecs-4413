import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password

class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_signup_success(self, client: TestClient, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/signup", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"]
        assert data["user"]["email"] == test_user_data["email"]
        assert data["token_type"] == "bearer"

    def test_signup_duplicate_username(self, client: TestClient, test_user, test_user_data):
        """Test signup with duplicate username."""
        response = client.post("/api/v1/auth/signup", json=test_user_data)
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_signup_duplicate_email(self, client: TestClient, test_user, test_user_data):
        """Test signup with duplicate email."""
        test_user_data["username"] = "different_username"
        response = client.post("/api/v1/auth/signup", json=test_user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_signup_invalid_data(self, client: TestClient):
        """Test signup with invalid data."""
        invalid_data = {
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid email
            "password": "123",  # Too short
            "first_name": "",
            "last_name": ""
        }
        response = client.post("/api/v1/auth/signup", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_login_success(self, client: TestClient, test_user, test_user_data):
        """Test successful login."""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == test_user_data["username"]

    def test_login_invalid_credentials(self, client: TestClient, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_inactive_user(self, client: TestClient, test_user, test_user_data, db_session: Session):
        """Test login with inactive user."""
        # Deactivate user
        test_user.is_active = False
        db_session.commit()
        
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Inactive user" in response.json()["detail"]

    def test_forgot_password_success(self, client: TestClient, test_user):
        """Test successful password reset request."""
        response = client.post("/api/v1/auth/password/forgot", json={"email": test_user.email})
        
        assert response.status_code == 200
        assert "password reset" in response.json()["message"].lower()

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """Test password reset request with non-existent email."""
        response = client.post("/api/v1/auth/password/forgot", json={"email": "nonexistent@example.com"})
        
        # Should return success message for security (don't reveal if email exists)
        assert response.status_code == 200

    def test_reset_password_success(self, client: TestClient, test_user, db_session: Session):
        """Test successful password reset."""
        from app.models.user import PasswordResetToken
        from app.core.security import get_password_hash
        from datetime import datetime, timedelta
        
        # Create a valid reset token
        reset_token = "valid_reset_token_123"
        token_record = PasswordResetToken(
            user_id=test_user.user_id,
            token_hash=get_password_hash(reset_token),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(token_record)
        db_session.commit()
        
        reset_data = {
            "token": reset_token,
            "new_password": "newpassword123"
        }
        response = client.post("/api/v1/auth/password/reset", json=reset_data)
        
        assert response.status_code == 200
        assert "Password has been reset successfully" in response.json()["message"]

    def test_reset_password_invalid_token(self, client: TestClient):
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid_token",
            "new_password": "newpassword123"
        }
        response = client.post("/api/v1/auth/password/reset", json=reset_data)
        
        assert response.status_code == 400
        assert "Invalid or expired reset token" in response.json()["detail"]

    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]

    def test_protected_endpoint_without_auth(self, client: TestClient):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code in [401, 403]  # FastAPI HTTPBearer may return 403

    def test_protected_endpoint_with_invalid_token(self, client: TestClient):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/me", headers=headers)
        
        assert response.status_code == 401
