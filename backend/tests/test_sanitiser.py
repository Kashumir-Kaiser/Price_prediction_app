"""Tests for SQL injection sanitiser."""
import pytest
from fastapi import HTTPException

from app.utils.sanitiser import sanitise_identifier


class TestSanitiseIdentifier:
    """Test sanitise_identifier function."""

    def test_clean_username_passes(self):
        """Test clean username passes through unchanged."""
        result = sanitise_identifier("john_doe_99")
        assert result == "john_doe_99"

    def test_username_with_whitespace_stripped(self):
        """Test username with whitespace is stripped."""
        result = sanitise_identifier("  john_doe  ")
        assert result == "john_doe"

    def test_sql_like_input_is_not_rejected(self):
        """Sanitiser is normalization + length checks, not SQL pattern blocking."""
        result = sanitise_identifier("admin'--")
        assert result == "admin'--"

    def test_semicolon_input_is_not_rejected(self):
        """Semicolons are allowed by this helper."""
        result = sanitise_identifier("user; DELETE FROM users")
        assert result == "user; DELETE FROM users"

    def test_too_long_rejected(self):
        """Test too long input rejected."""
        with pytest.raises(HTTPException) as exc_info:
            sanitise_identifier("a" * 300)
        assert exc_info.value.status_code == 400

    def test_null_bytes_removed(self):
        """Null bytes are stripped before return."""
        result = sanitise_identifier("ab\x00cd")
        assert result == "abcd"
