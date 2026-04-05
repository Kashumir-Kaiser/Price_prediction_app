"""Tests for admin seeding function."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.core.seed_admin import seed_admin_user


class TestSeedAdmin:
    """Test admin user seeding."""

    def _make_mock_db(self, existing_user=None):
        """Create a mock async DB session with configurable query result."""
        mock_db = AsyncMock()
        mock_db.add = Mock()

        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = existing_user
        mock_db.execute.return_value = mock_result

        return mock_db

    @pytest.mark.asyncio
    async def test_seed_admin_creates_user(self):
        """seed_admin creates the admin user when none exists."""
        mock_db = self._make_mock_db(existing_user=None)

        with patch('app.core.seed_admin.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            await seed_admin_user()

        # Verify user was added
        assert mock_db.add.called, "db.add() should have been called"
        call_args = mock_db.add.call_args[0][0]
        assert call_args.username == "admin"
        assert call_args.role == "admin"
        assert call_args.password_hash != "Admin@StockApp2025!"  # Should be hashed
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_seed_admin_idempotent(self):
        """Test seed_admin is idempotent — skips if admin exists."""
        existing_admin = Mock()
        existing_admin.username = "admin"
        mock_db = self._make_mock_db(existing_user=existing_admin)

        with patch('app.core.seed_admin.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
 
            await seed_admin_user()
 
        assert not mock_db.add.called, "db.add() should NOT have been called"
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_seed_admin_password_hashed(self):
        """Test seeded admin password is hashed, not plaintext."""
        mock_db = self._make_mock_db(existing_user=None)

        with patch('app.core.seed_admin.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
 
            await seed_admin_user()
 
        user_arg = mock_db.add.call_args[0][0]
        assert user_arg.password_hash.startswith("$"), "Expected a bcrypt hash"
        assert "Admin@StockApp2025!" not in user_arg.password_hash
