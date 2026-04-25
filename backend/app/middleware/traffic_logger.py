"""Traffic logging middleware for admin analytics."""
import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTask

from app.db.database import AsyncSessionLocal
from app.db.models import RequestLog

log = structlog.get_logger(__name__)


async def _write_log(
    method: str,
    path: str,
    status_code: int,
    duration_ms: int,
    client_ip: str,
    username: str | None,
) -> None:
    """Async background task -- writes one RequestLog row. Errors are logged, not raised."""
    try:
        async with AsyncSessionLocal() as db:
            db.add(RequestLog(
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                username=username,
            ))
            await db.commit()
    except Exception as exc:
        # Log the failure but do NOT propagate -- a logging failure must never
        # affect the API response that the user is waiting for.
        log.warning(
            "request_log_write_failed",
            error=str(exc),
            path=path,
            status=status_code,
        )


class TrafficLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request to the request_logs table via BackgroundTasks."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000)

        username = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                from app.services.auth_service import decode_token
                username = decode_token(auth[7:]).get("sub")
            except Exception:
                pass

        client_ip = request.client.host if request.client else "unknown"

        # Attach as a BackgroundTask -- runs AFTER the response is sent to client.
        # This ensures the response is never delayed by DB latency.
        response.background = BackgroundTask(
            _write_log,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_ip,
            username,
        )
        return response
