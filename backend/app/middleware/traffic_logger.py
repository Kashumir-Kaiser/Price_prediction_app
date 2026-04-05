"""Traffic logging middleware for admin analytics."""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.database import AsyncSessionLocal
from app.db.models import RequestLog


class TrafficLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request to the request_logs table."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000)

        # Extract user identity from JWT if present (best-effort, no exception on failure)
        username = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.services.auth_service import decode_token
                payload = decode_token(auth_header[7:])
                username = payload.get("sub")
            except Exception:
                pass  # Ignore decode errors

        # Write log asynchronously (fire-and-forget, do NOT await — avoid slowing response)
        try:
            async with AsyncSessionLocal() as db:
                log = RequestLog(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    client_ip=request.client.host if request.client else "unknown",
                    username=username,
                )
                db.add(log)
                await db.commit()
        except Exception:
            # Don't crash the request if logging fails
            pass

        return response
