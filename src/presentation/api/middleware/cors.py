"""CORS middleware setup.

Author: Juan [juankaspain]
Created: 2026-02-13
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI, allowed_origins: list[str]) -> None:
    """Configure CORS for dashboard access.
    
    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins (dashboard URLs)
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-RateLimit-*"],
    )
