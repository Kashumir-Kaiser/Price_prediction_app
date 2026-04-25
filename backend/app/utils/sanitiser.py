"""Input sanitization utilities."""
import re
from fastapi import HTTPException, status


def sanitise_identifier(value: str, field_name: str = "identifier") -> str:
    """
    Sanitize a user-supplied identifier string.

    Applies:
    1. Null byte removal (prevents C-style string attacks)
    2. Stripping leading/trailing whitespace
    3. Length validation

    Args:
        value: Raw input string
        field_name: Field name for error messages

    Returns:
        Sanitized string

    Raises:
        HTTPException: If input is invalid after sanitization
    """
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty.",
        )

    # Step 1: Remove null bytes
    cleaned = value.replace("\x00", "")

    # Step 2: Strip whitespace
    cleaned = cleaned.strip()

    # Step 3: Validate length after cleaning
    if len(cleaned) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty after sanitization.",
        )

    if len(cleaned) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} too long (max 128 characters).",
        )

    return cleaned


def sanitise_email(value: str) -> str:
    """Sanitize an email address."""
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email cannot be empty.",
        )

    cleaned = value.replace("\x00", "").strip().lower()

    if "@" not in cleaned or "." not in cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format.",
        )

    return cleaned
