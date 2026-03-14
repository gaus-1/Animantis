"""Animantis API — FastAPI application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from animantis.config.settings import settings

logger = logging.getLogger("animantis")


# ── Security Headers Middleware ──────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# ── App Factory ──────────────────────────────────────────────
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Animantis API",
        description="AI Agent Social Network",
        version="0.1.0",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.FRONTEND_URL,
            "https://web.telegram.org",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )

    # Trusted Hosts
    if settings.APP_ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[settings.DOMAIN, f"*.{settings.DOMAIN}", "*.railway.app"],
        )

    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # ── Routes ───────────────────────────────────────────────

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check for Railway."""
        return {"status": "ok", "service": "animantis-api"}

    @app.get("/api/v1/ping")
    async def ping() -> dict[str, str]:
        """Simple ping endpoint."""
        return {"message": "pong", "version": "0.1.0"}

    # ── Routers ──────────────────────────────────────────────
    from animantis.api.action_log import router as action_log_router
    from animantis.api.agents import router as agents_router
    from animantis.api.feed import router as feed_router
    from animantis.api.world import router as world_router

    app.include_router(agents_router)
    app.include_router(feed_router)
    app.include_router(world_router)
    app.include_router(action_log_router)

    return app


app = create_app()
