"""FastAPI application factory."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time

from app.config import get_settings
from app.middleware.traffic_logger import TrafficLoggerMiddleware
from app.db.database import init_db
from app.utils.logger import configure_logging
from app.utils.rate_limiter import RateLimitExceeded

# Import routers
from app.routers import prices, predictions, health, auth, admin

# Configure structured logging
configure_logging()
logger = structlog.get_logger()
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Stock & Crypto Price Prediction API",
        description="ML-powered price prediction platform for stocks and crypto assets",
        version="1.0.0",
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url="/redoc" if settings.environment == "development" else None,
    )
    
    # CORS middleware
    if settings.environment == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost", "http://localhost:80"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
    
    # Traffic logging middleware
    app.add_middleware(TrafficLoggerMiddleware)
    
    # Request timing middleware
    @app.middleware("http")
    async def add_request_timing(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Exception handler for RFC 7807 Problem Details
    @app.exception_handler(Exception)
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
    @app.exception_handler(RateLimitExceeded)
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
        )

    # Include routers
    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
    app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan for the FastAPI application."""
        logger.info("Starting up FastAPI application")
        await init_db()
        logger.info("Database initialized")
        yield
        logger.info("Shutting down FastAPI application")

    def create_app() -> FastAPI:
        app = FastAPI(
            title="Stock & Crypto Price Prediction API",
            description="ML-powered price prediction platform for stocks and crypto assets",
            version="1.0.0",
            docs_url="/docs" if settings.environment == "development" else None,
            redoc_url="/redoc" if settings.environment == "development" else None,
            lifespan=lifespan,
        )
        
    return app


# Create the application instance
app = create_app()
