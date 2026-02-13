"""FastAPI main application.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from redis.asyncio import Redis

from src.infrastructure.persistence.timescaledb import TimescaleDB
from src.presentation.api.middleware import (
    AuthMiddleware,
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    setup_cors,
)
from src.presentation.api.routes import (
    bots,
    health,
    metrics,
    orders,
    positions,
    risk,
    wallet,
)
from src.presentation.api.websocket import router as websocket_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    # Startup
    logger.info("startup_begin")
    
    # Initialize database
    db = TimescaleDB()
    await db.connect()
    app.state.db = db
    
    # Initialize Redis
    redis = Redis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True,
    )
    app.state.redis = redis
    
    logger.info("startup_complete")
    
    yield
    
    # Shutdown
    logger.info("shutdown_begin")
    
    await redis.close()
    await db.disconnect()
    
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Create FastAPI application.
    
    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="PETS API",
        description="Polymarket Elite Trading System API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Setup CORS
    setup_cors(
        app,
        allowed_origins=[
            "http://localhost:8501",  # Streamlit dashboard
            "http://dashboard:8501",  # Docker dashboard
        ],
    )
    
    # Add middleware (order matters - reverse execution order)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    # RateLimitMiddleware and AuthMiddleware added in dependencies
    
    # Include routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(bots.router, prefix="/api/v1")
    app.include_router(positions.router, prefix="/api/v1")
    app.include_router(orders.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    app.include_router(wallet.router, prefix="/api/v1")
    app.include_router(risk.router, prefix="/api/v1")
    app.include_router(websocket_router, prefix="/api/v1")
    
    logger.info("app_created", extra={"routes": len(app.routes)})
    
    return app


app = create_app()
