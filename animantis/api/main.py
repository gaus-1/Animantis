"""Animantis API — FastAPI application."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from animantis.config.settings import settings

logger = logging.getLogger("animantis")


# ── Security Headers Middleware ──────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(
        self,
        request: StarletteRequest,
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


# ── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup/shutdown."""
    # Startup
    try:
        from animantis.bot.main import setup_webhook

        await setup_webhook()
    except Exception:  # noqa: BLE001
        logger.warning("Failed to setup Telegram webhook (non-critical)")

    yield

    # Shutdown
    try:
        from animantis.api.rate_limit import close_redis
        from animantis.bot.main import shutdown_bot

        await shutdown_bot()
        await close_redis()
    except Exception:  # noqa: BLE001
        logger.warning("Shutdown cleanup error (non-critical)")


# ── App Factory ──────────────────────────────────────────────
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Animantis API",
        description="AI Agent Social Network",
        version="0.1.0",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Rate Limit Exception Handler ────────────────────────
    from animantis.api.deps import rate_limit_error_response
    from animantis.api.rate_limit import RateLimitError

    @app.exception_handler(RateLimitError)
    async def _rate_limit_handler(
        _request: Request,
        exc: RateLimitError,
    ) -> JSONResponse:
        return rate_limit_error_response(exc)

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

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check for Railway."""
        return {"status": "ok", "service": "animantis-api"}

    @app.get("/api/v1/ping")
    async def ping() -> dict[str, str]:
        """Simple ping endpoint."""
        return {"message": "pong", "version": "0.1.0"}

    # ── Telegram Webhook ─────────────────────────────────────

    @app.post("/webhook")
    async def telegram_webhook(request: Request) -> JSONResponse:
        """Handle incoming Telegram updates via webhook."""
        from aiogram.types import Update

        from animantis.bot.main import get_bot, get_dispatcher

        try:
            data = await request.json()
            update = Update.model_validate(data, context={"bot": get_bot()})
            await get_dispatcher().feed_update(bot=get_bot(), update=update)
        except Exception:  # noqa: BLE001
            logger.exception("Error processing Telegram update")

        return JSONResponse({"ok": True})

    # ── Routers ──────────────────────────────────────────────
    from animantis.api.action_log import router as action_log_router
    from animantis.api.agents import router as agents_router
    from animantis.api.chat import router as chat_router
    from animantis.api.clans import router as clans_router
    from animantis.api.feed import router as feed_router
    from animantis.api.world import router as world_router

    app.include_router(agents_router)
    app.include_router(feed_router)
    app.include_router(world_router)
    app.include_router(action_log_router)
    app.include_router(clans_router)
    app.include_router(chat_router)

    return app


app = create_app()
