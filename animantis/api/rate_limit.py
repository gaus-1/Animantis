"""Rate limiting via Redis — sliding window counter."""

import logging
import time

from redis.asyncio import Redis  # type: ignore[import-untyped]

from animantis.config.settings import settings

logger = logging.getLogger("animantis")

_redis: Redis | None = None


async def _get_redis() -> Redis:
    """Get or create Redis connection (lazy singleton)."""
    global _redis  # noqa: PLW0603
    if _redis is None:
        _redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s.")


async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    """Check rate limit using Redis sliding window.

    Args:
        key: Unique key (e.g. "api:user:123" or "chat:user:456").
        limit: Max requests allowed in the window.
        window_seconds: Time window in seconds.

    Raises:
        RateLimitExceeded: If limit is exceeded.
    """
    try:
        redis = await _get_redis()
        now = time.time()
        window_start = now - window_seconds

        pipe = redis.pipeline()
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries
        pipe.zcard(key)
        # Add new entry
        pipe.zadd(key, {str(now): now})
        # Set expiry on key
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1]
        if current_count >= limit:
            # Find oldest entry to calculate retry time
            oldest = await redis.zrange(key, 0, 0, withscores=True)
            retry_after = int(oldest[0][1] + window_seconds - now) + 1 if oldest else window_seconds
            raise RateLimitError(retry_after=max(retry_after, 1))
    except RateLimitError:
        raise
    except Exception:  # noqa: BLE001
        # Redis down — fail open (allow request)
        logger.warning("Redis rate limit unavailable, allowing request")


async def close_redis() -> None:
    """Close Redis connection on shutdown."""
    global _redis  # noqa: PLW0603
    if _redis:
        await _redis.close()
        _redis = None
