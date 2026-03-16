"""FastAPI dependencies — rate limiting, auth (future)."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from animantis.api.rate_limit import RateLimitError, check_rate_limit
from animantis.config.settings import settings

logger = logging.getLogger("animantis")


def _client_ip(request: Request) -> str:
    """Extract client IP from request (X-Forwarded-For or direct)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def rate_limit_api(request: Request) -> None:
    """General API rate limit: settings.RATE_LIMIT_API req/min."""
    ip = _client_ip(request)
    await check_rate_limit(
        key=f"rl:api:{ip}",
        limit=settings.RATE_LIMIT_API,
        window_seconds=60,
    )


async def rate_limit_agent_create(request: Request) -> None:
    """Agent creation rate limit: settings.RATE_LIMIT_AGENT_CREATE per hour."""
    ip = _client_ip(request)
    await check_rate_limit(
        key=f"rl:create:{ip}",
        limit=settings.RATE_LIMIT_AGENT_CREATE,
        window_seconds=3600,
    )


async def rate_limit_chat(request: Request) -> None:
    """Chat rate limit: settings.RATE_LIMIT_CHAT per min."""
    ip = _client_ip(request)
    await check_rate_limit(
        key=f"rl:chat:{ip}",
        limit=settings.RATE_LIMIT_CHAT,
        window_seconds=60,
    )


def rate_limit_error_response(exc: RateLimitError) -> JSONResponse:
    """Build 429 response for rate limit exceeded."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests",
            "retry_after": exc.retry_after,
        },
        headers={"Retry-After": str(exc.retry_after)},
    )
