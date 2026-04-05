"""Tests for authentication service."""
import pytest
from unittest.mock import Mock, AsyncMock
from jose import JWTError

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_user_by_username,
    create_user,
)


class TestPasswordHelpers:
    """Test password hashing and verification."""

    def test_hash_password_returns_bcrypt_string(self):
        """Test that hash_password returns a bcrypt hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed.startswith("$2")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """Test verify_password returns False for wrong password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False


class TestJWTHelpers:
    """Test JWT token creation and decoding."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a JWT string."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 20
        # JWT has 3 parts separated by dots
        assert token.count(".") == 2

    def test_decode_token_valid(self):
        """Test decode_token returns correct payload."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "user"
        assert "exp" in decoded

    def test_decode_token_invalid_raises_jwt_error(self):
        """Test decode_token raises JWTError for invalid token."""
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_decode_token_tampered_raises_jwt_error(self):
        """Test decode_token raises JWTError for tampered token."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(JWTError):
            decode_token(tampered)


class TestDBHelpers:
    """Test database helper functions."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_found(self):
        """Test get_user_by_username returns user when found."""
        mock_user = Mock()
        mock_user.username = "testuser"

        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user = await get_user_by_username(mock_db, "testuser")

        assert user == mock_user

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self):
        """Test get_user_by_username returns None when not found."""
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        user = await get_user_by_username(mock_db, "nonexistent")

        assert user is None

    @pytest.mark.asyncio
    async def test_create_user_hashes_password(self):
        """Test create_user stores hashed password, not plaintext."""
        mock_db = AsyncMock()

        user = await create_user(
            mock_db,
            username="testuser",
            email="test@example.com",
            password="plaintext123"
        )

        # Password should be hashed, not equal to plaintext
        assert user.password_hash != "plaintext123"
        assert user.password_hash.startswith("$")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"

        mock_db.add.assert_called_once_with(user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(user)
