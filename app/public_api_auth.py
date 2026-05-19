"""Public API authentication using API key header."""
from fastapi import HTTPException, Request, status

from app.config import settings
from app.rate_limiter import RateLimiter

# Rate limiter for API endpoints (100 requests per minute per IP)
_api_rate_limiter = RateLimiter()


async def require_api_key(request: Request) -> None:
    """FastAPI dependency — raises 401 if API key is invalid or missing.

    Also checks if the public API is enabled.
    """
    # Check if API is enabled
    if not settings.api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public API is disabled"
        )

    # Rate limit by IP
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    allowed = await _api_rate_limiter.check(f"api:{client_ip}", 100)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    # Validate API key from header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required"
        )

    # Simple constant-time comparison
    if not _constant_time_compare(api_key, settings.api_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )


def _constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
