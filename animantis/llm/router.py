"""YandexGPT client with retry, fallback, and caching."""

import hashlib
import json
import logging
from dataclasses import dataclass

import httpx
from redis.asyncio import ConnectionPool, Redis  # type: ignore[import-untyped]

from animantis.config.settings import settings

logger = logging.getLogger("animantis")

# ── Response ─────────────────────────────────────────────────


@dataclass
class LLMResponse:
    """Structured response from LLM."""

    text: str
    model: str
    tokens_used: int
    cached: bool = False


# ── Connection Pools (module-level singletons) ──────────────

_http_client: httpx.AsyncClient | None = None
_redis_pool: ConnectionPool | None = None

YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30


def _get_http_client() -> httpx.AsyncClient:
    """Get or create a pooled httpx client."""
    global _http_client  # noqa: PLW0603
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=30,
            ),
        )
    return _http_client


def _get_redis() -> Redis:
    """Get Redis client backed by a shared connection pool."""
    global _redis_pool  # noqa: PLW0603
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=10,
            decode_responses=True,
        )
    return Redis(connection_pool=_redis_pool)


async def close_pools() -> None:
    """Close connection pools on shutdown. Call from FastAPI lifespan."""
    global _http_client, _redis_pool  # noqa: PLW0603
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
    logger.info("LLM connection pools closed")


# ── YandexGPT Client ────────────────────────────────────────


async def _call_yandex_gpt(
    messages: list[dict[str, str]],
    model_uri: str,
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> LLMResponse:
    """Call YandexGPT API with retry logic.

    Args:
        messages: List of {role, text} messages.
        model_uri: Model URI (gpt://folder/model/version).
        temperature: Sampling temperature.
        max_tokens: Max tokens in response.

    Returns:
        LLMResponse with text, model, tokens.

    Raises:
        LLMError: If all retries exhausted.
    """
    payload = {
        "modelUri": model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": str(max_tokens),
        },
        "messages": messages,
    }
    headers = {
        "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    client = _get_http_client()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = await client.post(YANDEX_API_URL, json=payload, headers=headers)
            resp.raise_for_status()

            data = resp.json()
            result = data["result"]
            text = result["alternatives"][0]["message"]["text"]
            tokens = int(result.get("usage", {}).get("totalTokens", 0))

            logger.info(
                "LLM response",
                extra={
                    "model": model_uri,
                    "tokens": tokens,
                    "attempt": attempt,
                },
            )
            return LLMResponse(text=text, model=model_uri, tokens_used=tokens)

        except httpx.TimeoutException as e:
            last_error = e
            logger.warning("LLM timeout", extra={"attempt": attempt, "model": model_uri})
        except httpx.HTTPStatusError as e:
            last_error = e
            logger.warning(
                "LLM HTTP error",
                extra={"status": e.response.status_code, "attempt": attempt},
            )
            if e.response.status_code == 429:
                import asyncio

                await asyncio.sleep(attempt * 2)
        except Exception as e:  # noqa: BLE001
            last_error = e
            logger.warning("LLM unexpected error", extra={"error": str(e), "attempt": attempt})

    msg = f"LLM failed after {MAX_RETRIES} retries: {last_error}"
    raise LLMError(msg)


# ── High-Level Functions ────────────────────────────────────


async def generate_tick(
    messages: list[dict[str, str]],
    cache_key: str | None = None,
) -> LLMResponse:
    """Generate agent tick response using YandexGPT Lite."""
    if cache_key:
        cached = await _get_cache(cache_key)
        if cached:
            return cached

    try:
        response = await _call_yandex_gpt(
            messages=messages,
            model_uri=settings.yandex_gpt_lite_uri,
            temperature=0.8,
            max_tokens=400,
        )
    except LLMError:
        logger.warning("YandexGPT Lite failed, falling back to rest action")
        response = LLMResponse(
            text='{"action": "rest", "emotion": "tired", "content": "..."}',
            model="fallback",
            tokens_used=0,
        )

    if cache_key and response.model != "fallback":
        await _set_cache(cache_key, response)

    return response


async def generate_chat(
    messages: list[dict[str, str]],
) -> LLMResponse:
    """Generate chat response using YandexGPT Pro."""
    return await _call_yandex_gpt(
        messages=messages,
        model_uri=settings.yandex_gpt_pro_uri,
        temperature=0.7,
        max_tokens=800,
    )


# ── Cache ────────────────────────────────────────────────────

CACHE_TTL = 600  # 10 minutes


def _make_cache_hash(key: str) -> str:
    """Create short hash for cache key."""
    return f"llm:cache:{hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()[:16]}"


async def _get_cache(key: str) -> LLMResponse | None:
    """Get cached LLM response from Redis (pooled)."""
    try:
        redis = _get_redis()
        data = await redis.get(_make_cache_hash(key))

        if data:
            parsed = json.loads(data)
            logger.info("LLM cache hit", extra={"key": key[:30]})
            return LLMResponse(
                text=parsed["text"],
                model=parsed["model"],
                tokens_used=0,
                cached=True,
            )
    except Exception:  # noqa: BLE001
        logger.warning("Redis cache read error")
    return None


async def _set_cache(key: str, response: LLMResponse) -> None:
    """Cache LLM response in Redis (pooled)."""
    try:
        redis = _get_redis()
        data = json.dumps({"text": response.text, "model": response.model})
        await redis.setex(_make_cache_hash(key), CACHE_TTL, data)
    except Exception:  # noqa: BLE001
        logger.warning("Redis cache write error")


# ── Errors ───────────────────────────────────────────────────


class LLMError(Exception):
    """LLM call failed after all retries."""
