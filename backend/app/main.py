"""FastAPI application factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import structlog
import time

from app.config import get_settings
from app.middleware.traffic_logger import TrafficLoggerMiddleware
from app.db.database import engine
from app.utils.logger import configure_logging
from app.utils.rate_limiter import RateLimitExceeded

# Import routers
from app.routers import prices, predictions, health, auth, admin

# Configure structured logging
configure_logging()
logger = structlog.get_logger()
settings = get_settings()

API_V1 = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # Startup
    logger.info("[lifespan] Starting up FastAPI application")
    yield
    # Shutdown -- close DB connection pool cleanly
    logger.info("[lifespan] Shutting down FastAPI application")
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="Market Analysis API",
        version="1.0.0",
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url="/redoc" if settings.environment == "development" else None,
        lifespan=lifespan,  # attached once, correctly
    )

    # CORS middleware
    if settings.environment == "development":
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins.split(",") if hasattr(settings, "cors_origins") else ["http://localhost", "http://localhost:80"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

    # Traffic logging middleware
    application.add_middleware(TrafficLoggerMiddleware)

    # Request timing middleware
    @application.middleware("http")
    async def add_request_timing(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Exception handler for RFC 7807 Problem Details
    @application.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": str(exc),
                "instance": request.url.path,
            },
        )

    # Exception handler for RateLimitExceeded
    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "type": "about:blank",
                "title": "Too Many Requests",
                "status": 429,
                "detail": str(exc),
                "instance": request.url.path,
            },
            headers={"Retry-After": "60"},
        )

    # Include routers with versioned prefix
    application.include_router(health.router, prefix=API_V1, tags=["health"])
    application.include_router(auth.router, prefix=API_V1, tags=["auth"])
    application.include_router(admin.router, prefix=API_V1, tags=["admin"])
    application.include_router(prices.router, prefix=API_V1, tags=["prices"])
    application.include_router(predictions.router, prefix=API_V1, tags=["predictions"])

    # Legacy redirect: /api/* -> /api/v1/* during migration window
    @application.get("/api/{path:path}", include_in_schema=False)
    async def legacy_redirect(path: str):
        """
        Redirect /api/* to /api/v1/* during migration window.
        Remove this after all frontend clients use /api/v1/ paths.
        """
        return RedirectResponse(url=f"/api/v1/{path}", status_code=307)

    return application


# Module-level app object used by uvicorn
app = create_app()
