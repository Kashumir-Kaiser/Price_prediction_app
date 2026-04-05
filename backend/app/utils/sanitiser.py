"""Input sanitisation utility for SQL injection protection."""
import re
import html
from fastapi import HTTPException

# Patterns that indicate SQL injection attempts
_SQL_PATTERNS = re.compile(
    r"(--|;|'|\"|/\*|\*/|xp_|UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO"
    r"|DELETE\s+FROM|UPDATE\s+\w+\s+SET|EXEC\s*\(|CAST\s*\(|CONVERT\s*\()",
    re.IGNORECASE,
)


def sanitise_identifier(value: str, field_name: str = "input") -> str:
    """
    Validate that value contains no SQL injection metacharacters.

    Raises HTTP 422 if suspicious content is detected.
    Use for username / email fields coming from untrusted form data.

    Args:
        value: The input string to sanitize
        field_name: Name of the field for error messages

    Returns:
        The sanitized (stripped) string

    Raises:
        HTTPException: 422 if SQL injection patterns detected
    """
    stripped = html.unescape(value.strip())

    if _SQL_PATTERNS.search(stripped):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid characters detected in {field_name}.",
        )

    if len(stripped) > 255:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} exceeds maximum length.",
        )

    return stripped
