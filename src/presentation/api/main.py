"""FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.presentation.api.routes import analytics, bots, markets, orders, positions, paper

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("FastAPI app starting up")
    yield
    # Shutdown
    logger.info("FastAPI app shutting down")


# Create FastAPI app
app = FastAPI(
    title="PETS - Polymarket Elite Trading System",
    description="API for automated Polymarket trading with Bot 8 Volatility Skew strategy",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware (allow Streamlit dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit default
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError as 400 Bad Request."""
    logger.warning(
        "ValueError",
        extra={
            "path": request.url.path,
            "error": str(exc),
        },
    )
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions as 500 Internal Server Error."""
    logger.error(
        "Unexpected error",
        extra={
            "path": request.url.path,
            "error": str(exc),
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PETS API"}


# Include routers
app.include_router(bots.router, prefix="/api/bots", tags=["Bots"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
app.include_router(markets.router, prefix="/api/markets", tags=["Markets"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(paper.router, prefix="/api/paper", tags=["Paper Trading"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "PETS - Polymarket Elite Trading System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
