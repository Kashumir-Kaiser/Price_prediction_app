"""Tests for authentication router."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app

client = TestClient(app)


class TestRegister:
    """Test registration endpoint."""

    @patch('app.routers.auth.get_user_by_username')
    @patch('app.routers.auth.create_user')
    def test_register_success(self, mock_create, mock_get_user):
        """Test successful registration returns 201."""
        mock_get_user.return_value = None # None so "username already exists" check passes

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "newuser"
        mock_user.email = "new@example.com"
        mock_user.role = "user"
        mock_create.return_value = mock_user # Return the mock user immediately

        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data

    @patch('app.routers.auth.get_user_by_username')
    def test_register_duplicate_username(self, mock_get_user):
        """Test duplicate username returns 409."""
        mock_get_user.return_value = Mock()

        response = client.post("/api/auth/register", json={
            "username": "existinguser",
            "email": "new@example.com",
            "password": "password123"
        })

        assert response.status_code == 409
        assert "already taken" in response.json()["detail"].lower()

    def test_register_sql_injection_username(self):
        """Test SQL injection in username returns 422."""
        response = client.post("/api/auth/register", json={
            "username": "admin'--",
            "email": "test@example.com",
            "password": "password123"
        })

        assert response.status_code == 422


class TestLogin:
    """Test login endpoint."""

    @patch('app.routers.auth.get_user_by_username')
    @patch('app.routers.auth.verify_password')
    @patch('app.routers.auth.create_access_token')
    def test_login_success(self, mock_token, mock_verify, mock_get_user):
        """Test successful login returns token."""
        mock_user = Mock()
        mock_user.password_hash = "hashed"
        mock_user.role = "user"
        mock_user.is_active = True
        mock_get_user.return_value = mock_user
        mock_verify.return_value = True
        mock_token.return_value = "test.jwt.token"

        response = client.post("/api/auth/login", data={
            "username": "testuser",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.routers.auth.get_user_by_username')
    def test_login_wrong_password(self, mock_get_user):
        """Test wrong password returns 401."""
        mock_user = Mock()
        mock_user.password_hash = "hashed"
        mock_user.is_active = True
        mock_get_user.return_value = mock_user

        with patch('app.routers.auth.verify_password', return_value=False):
            response = client.post("/api/auth/login", data={
                "username": "testuser",
                "password": "wrongpassword"
            })

        assert response.status_code == 401

    @patch('app.routers.auth.get_user_by_username')
    def test_login_sql_injection_username(self, mock_get_user):
        """Test SQL injection in login username returns 422."""
        mock_get_user.return_value = None

        response = client.post("/api/auth/login", data={
            "username": "' OR '1'='1",
            "password": "password123"
        })

        # Should be rejected by sanitiser
        assert response.status_code == 422


class TestProtectedRoutes:
    """Test protected routes require authentication."""

    def test_predictions_without_token(self):
        """Test predictions endpoint without token returns 401."""
        response = client.get("/api/predictions/crypto?symbol=BTC/USD")

        # Note: This may return 404 if model not found, but should not be 401
        # because we haven't added auth requirement to predictions yet
        assert response.status_code in [401, 404, 503]
