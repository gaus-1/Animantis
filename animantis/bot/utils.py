"""Shared utilities for bot handlers."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.config.settings import settings
from animantis.db.connection import async_session as async_session_factory
from animantis.db.models import Agent, User, Zone

__all__ = [
    "_get_or_create_user",
    "_get_user_agents",
    "_get_zone_name",
    "_mood_emoji",
    "async_session_factory",
]

logger = logging.getLogger("animantis")

MOOD_MAP: dict[str, str] = {
    "neutral": "😐",
    "happy": "😊",
    "sad": "😢",
    "angry": "😠",
    "inspired": "✨",
    "anxious": "😰",
    "proud": "😤",
    "bored": "😴",
}


async def _get_or_create_user(
    db: AsyncSession,
    telegram_id: int,
    username: str | None,
) -> User:
    """Get existing user or create a new one."""
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id),
    )
    user = result.scalar_one_or_none()

    changed = False
    if user:
        if username and user.username != username:
            user.username = username
            changed = True

        if telegram_id == settings.ADMIN_TELEGRAM and user.plan != "ultra":
            user.plan = "ultra"
            changed = True

        if changed:
            await db.commit()
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        plan="ultra" if telegram_id == settings.ADMIN_TELEGRAM else "free",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _get_user_agents(db: AsyncSession, user_id: int) -> list[Agent]:
    """Get all alive agents for a user."""
    result = await db.execute(
        select(Agent)
        .where(Agent.user_id == user_id, Agent.is_alive.is_(True))
        .order_by(Agent.created_at.desc()),
    )
    return list(result.scalars().all())


async def _get_zone_name(zone_id: int | None) -> str:
    """Get zone name by ID."""
    if not zone_id:
        return "Неизвестно"
    async with async_session_factory() as db:
        result = await db.execute(select(Zone).where(Zone.id == zone_id))
        zone = result.scalar_one_or_none()
        return zone.name if zone else "Неизвестно"


def _mood_emoji(mood: str) -> str:
    """Get emoji for agent mood."""
    return MOOD_MAP.get(mood, "🤔")
