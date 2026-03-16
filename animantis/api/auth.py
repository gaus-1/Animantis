"""Auth — Telegram initData HMAC-SHA256 verification.

Telegram Mini App sends initData string via X-Telegram-Init-Data header.
We verify it using HMAC-SHA256 with the bot token as the secret key.

Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import logging
import time
from typing import Annotated
from urllib.parse import parse_qs, unquote

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.config.settings import settings
from animantis.db.connection import get_db
from animantis.db.models import User

logger = logging.getLogger("animantis")

# initData TTL — 1 hour
INIT_DATA_TTL = 3600


def validate_init_data(init_data: str) -> dict:
    """Validate Telegram initData string using HMAC-SHA256.

    Args:
        init_data: URL-encoded query string from Telegram Mini App.

    Returns:
        Parsed user data dict with at minimum {"id": int, ...}.

    Raises:
        ValueError: If validation fails.
    """
    if not init_data:
        msg = "Empty initData"
        raise ValueError(msg)

    # Parse query string
    parsed = parse_qs(init_data, keep_blank_values=True)

    # Extract hash
    received_hash = parsed.pop("hash", [None])[0]
    if not received_hash:
        msg = "Missing hash in initData"
        raise ValueError(msg)

    # Check auth_date TTL
    auth_date_str = parsed.get("auth_date", [None])[0]
    if not auth_date_str:
        msg = "Missing auth_date in initData"
        raise ValueError(msg)

    try:
        auth_date = int(auth_date_str)
    except (ValueError, TypeError) as e:
        msg = "Invalid auth_date"
        raise ValueError(msg) from e

    if time.time() - auth_date > INIT_DATA_TTL:
        msg = "initData expired"
        raise ValueError(msg)

    # Build data-check-string: sorted key=value pairs joined by \n
    data_check_parts = []
    for key in sorted(parsed):
        values = parsed[key]
        val = values[0] if values else ""
        data_check_parts.append(f"{key}={val}")
    data_check_string = "\n".join(data_check_parts)

    # HMAC-SHA256 verification
    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        settings.TELEGRAM_BOT_TOKEN.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # computed_hash = HMAC-SHA256(secret_key, data_check_string)
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        msg = "Invalid initData signature"
        raise ValueError(msg)

    # Extract user data
    user_raw = parsed.get("user", [None])[0]
    if not user_raw:
        msg = "Missing user in initData"
        raise ValueError(msg)

    try:
        user_data = json.loads(unquote(user_raw))
    except (json.JSONDecodeError, TypeError) as e:
        msg = "Invalid user JSON in initData"
        raise ValueError(msg) from e

    if "id" not in user_data:
        msg = "Missing user id in initData"
        raise ValueError(msg)

    return user_data


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    x_telegram_init_data: Annotated[str | None, Header()] = None,
) -> User:
    """FastAPI dependency — validate initData and return User.

    Raises 401 if no initData or invalid.
    Creates user if not exists.
    """
    if settings.APP_ENV in ("test", "development") and settings.DEBUG and not x_telegram_init_data:
        # In dev/test with DEBUG, allow unauthenticated requests
        return await _get_or_create_user(db, telegram_id=0, username="dev_user")

    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Init-Data header")

    try:
        user_data = validate_init_data(x_telegram_init_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    telegram_id = user_data["id"]
    username = user_data.get("username", "")
    first_name = user_data.get("first_name", "")

    return await _get_or_create_user(
        db,
        telegram_id=telegram_id,
        username=username or first_name or f"user_{telegram_id}",
    )


async def _get_or_create_user(
    db: AsyncSession,
    telegram_id: int,
    username: str,
) -> User:
    """Get existing user by telegram_id or create new one."""
    query = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    await db.flush()
    return user
