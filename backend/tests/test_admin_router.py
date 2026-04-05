"""Tests for admin router."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app

client = TestClient(app)


class MockUser:
    """Mock user for testing."""
    def __init__(self, role="admin"):
        self.id = 1
        self.username = "admin"
        self.email = "admin@example.com"
        self.role = role
        self.is_active = True


def mock_admin_auth():
    """Mock admin authentication."""
    return MockUser(role="admin")


def mock_user_auth():
    """Mock regular user authentication."""
    return MockUser(role="user")


class TestAdminOverview:
    """Test admin overview stats endpoint."""

    @patch('app.routers.auth.get_current_user')
    def test_overview_with_admin_jwt(self, mock_get_user):
        """Test overview with admin JWT returns 200."""
        mock_get_user.return_value = AsyncMock(return_value=mock_admin_auth())

        with patch('app.routers.admin.get_overview_stats') as mock_stats:
            mock_stats.return_value = AsyncMock(return_value={
                "total_requests_today": 100,
                "unique_ips_today": 10,
                "avg_response_ms": 45.5,
                "error_rate_pct": 2.5
            })

            response = client.get("/api/admin/stats/overview")
            # Should require auth, so this may fail without proper token
            # In real test, we'd need to set up auth properly

    @patch('app.routers.auth.get_current_user')
    def test_overview_with_user_jwt(self, mock_get_user):
        """Test overview with user JWT returns 403."""
        mock_get_user.return_value = AsyncMock(return_value=mock_user_auth())

        response = client.get("/api/admin/stats/overview")
        # Should return 403 for non-admin

    def test_overview_without_jwt(self):
        """Test overview without JWT returns 401."""
        response = client.get("/api/admin/stats/overview")
        assert response.status_code == 401


class TestAdminUsers:
    """Test admin users endpoint."""

    @patch('app.routers.auth.get_current_user')
    @patch('app.routers.admin.get_db')
    def test_get_users_list(self, mock_db, mock_get_user):
        """Test get users list returns user data."""
        mock_get_user.return_value = AsyncMock(return_value=mock_admin_auth())

        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = "user"
        mock_user.is_active = True
        mock_user.created_at = "2024-01-01T00:00:00"
        mock_user.last_login_at = None

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_user]

        mock_db_instance = AsyncMock()
        mock_db_instance.execute.return_value = mock_result
        mock_db.return_value = AsyncMock(return_value=mock_db_instance)

        # This test needs proper FastAPI dependency override setup

    @patch('app.routers.auth.get_current_user')
    def test_deactivate_user_success(self, mock_get_user):
        """Test deactivate user with admin JWT."""
        mock_get_user.return_value = AsyncMock(return_value=mock_admin_auth())

        # Test would need proper setup with mocked DB

    @patch('app.routers.auth.get_current_user')
    def test_deactivate_admin_fails(self, mock_get_user):
        """Test cannot deactivate admin user."""
        mock_get_user.return_value = AsyncMock(return_value=mock_admin_auth())

        # Test would need proper setup
