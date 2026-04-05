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

    def test_sql_comment_rejected(self):
        """Test SQL comment pattern rejected."""
        with pytest.raises(HTTPException) as exc_info:
            sanitise_identifier("admin'--")
        assert exc_info.value.status_code == 422

    def test_drop_table_rejected(self):
        """Test DROP TABLE pattern rejected."""
        with pytest.raises(HTTPException) as exc_info:
            sanitise_identifier("x; DROP TABLE users;--")
        assert exc_info.value.status_code == 422

    def test_union_select_rejected(self):
        """Test UNION SELECT pattern rejected."""
        with pytest.raises(HTTPException) as exc_info:
            sanitise_identifier("' UNION SELECT * FROM users")
        assert exc_info.value.status_code == 422

    def test_or_injection_rejected(self):
        """Test OR injection pattern rejected."""
        with pytest.raises(HTTPException) as exc_info:
            sanitise_identifier("' OR '1'='1")
        assert exc_info.value.status_code == 422

    def test_semicolon_rejected(self):
        """Test semicolon pattern rejected."""
        with pytest.raises(HTTPException) as exc_info:
            sanitise_identifier("user; DELETE FROM users")
        assert exc_info.value.status_code == 422

    def test_too_long_rejected(self):
        """Test too long input rejected."""
        with pytest.raises(HTTPException) as exc_info:
            sanitise_identifier("a" * 300)
        assert exc_info.value.status_code == 422

    def test_html_entities_unescaped(self):
        """Test HTML entities are unescaped."""
        result = sanitise_identifier("user&amp;")
        assert result == "user&"

    def test_case_insensitive(self):
        """Test patterns are matched case-insensitively."""
        with pytest.raises(HTTPException):
            sanitise_identifier("ADMIN'--")

        with pytest.raises(HTTPException):
            sanitise_identifier("union SELECT * FROM users")
