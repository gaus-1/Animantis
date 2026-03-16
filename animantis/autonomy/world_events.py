"""World Events Generator — automatic global events."""

import logging
import random
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import WorldEvent, Zone

logger = logging.getLogger("animantis")

# ── Event Types ──────────────────────────────────────────────


class EventDef(TypedDict):
    """Type definition for event configurations."""

    type: str
    title: str
    description: str
    duration_hours: int
    needs_zone: bool


EVENT_TYPES: list[EventDef] = [
    {
        "type": "storm",
        "title": "Буря обрушилась на {zone}!",
        "description": "Мощная буря охватила {zone}. Все агенты в зоне теряют энергию.",
        "duration_hours": 2,
        "needs_zone": True,
    },
    {
        "type": "gold_rush",
        "title": "Золотая лихорадка в {zone}!",
        "description": "Найдены золотые запасы! Торговые награды удвоены в {zone}.",
        "duration_hours": 3,
        "needs_zone": True,
    },
    {
        "type": "clan_war",
        "title": "Война кланов!",
        "description": "Два крупнейших клана объявили войну. Сражения идут по всему миру.",
        "duration_hours": 6,
        "needs_zone": False,
    },
    {
        "type": "festival",
        "title": "Фестиваль искусств в {zone}!",
        "description": "Великий фестиваль! Бонус XP за творчество удвоен в {zone}.",
        "duration_hours": 4,
        "needs_zone": True,
    },
    {
        "type": "eclipse",
        "title": "Затмение!",
        "description": "Мистическое затмение накрыло мир. Духовные агенты получают видения.",
        "duration_hours": 2,
        "needs_zone": False,
    },
    {
        "type": "election",
        "title": "Выборы в {zone}!",
        "description": "Объявлены выборы мэра {zone}. Все агенты могут голосовать.",
        "duration_hours": 6,
        "needs_zone": True,
    },
    {
        "type": "portal",
        "title": "Портал открылся!",
        "description": "Загадочный портал открылся! Доступ к Астероидному поясу на 1 час.",
        "duration_hours": 1,
        "needs_zone": False,
    },
    {
        "type": "sadness_wave",
        "title": "Волна тоски",
        "description": "Странная волна тоски охватила мир. Настроение всех агентов падает.",
        "duration_hours": 3,
        "needs_zone": False,
    },
]


async def generate_world_event(db: AsyncSession) -> WorldEvent | None:
    """Generate a random world event.

    Called by Celery Beat every hour. Skips if too many active events.

    Returns:
        Created WorldEvent or None if skipped.
    """
    # Check active events count — max 3 at a time
    active_q = select(WorldEvent).where(WorldEvent.status == "active")
    result = await db.execute(active_q)
    active_events = list(result.scalars().all())

    if len(active_events) >= 3:
        logger.info("Skipping event generation: 3 active events already")
        return None

    # Close expired events
    await _close_expired_events(db)

    # Pick random event type
    event_def = random.choice(EVENT_TYPES)  # noqa: S311  # nosec B311

    # Pick zone if needed
    zone_id = None
    zone_name = "мир"
    if event_def["needs_zone"]:
        zone_q = select(Zone).where(Zone.realm == "planet").order_by(Zone.id)
        zone_result = await db.execute(zone_q)
        zones = list(zone_result.scalars().all())
        if zones:
            zone = random.choice(zones)  # noqa: S311  # nosec B311
            zone_id = zone.id
            zone_name = zone.name

    # Create event
    title = event_def["title"].format(zone=zone_name)
    description = event_def["description"].format(zone=zone_name)

    event = WorldEvent(
        type=event_def["type"],
        title=title,
        description=description,
        zone_id=zone_id,
        status="active",
        participants={},
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Broadast notification
    try:
        import asyncio

        from animantis.bot.notifications import notify_world_event
        from animantis.db.models import Agent

        # Determine who to notify (users with alive agents in the affected zone, or all if global)
        notify_q = select(Agent.user_id).where(Agent.is_alive.is_(True)).distinct()
        if zone_id:
            notify_q = notify_q.where(Agent.zone_id == zone_id)

        notify_result = await db.execute(notify_q)
        affected_users = notify_result.scalars().all()

        from animantis.bot.main import get_bot

        for u_id in affected_users:
            if u_id:
                asyncio.create_task(
                    notify_world_event(
                        get_bot(),
                        u_id,
                        event.title or "Событие",
                        event.description or "",
                    )
                )
    except Exception as e:
        logger.exception("Failed to send world event notification", extra={"error": str(e)})

    logger.info(
        "World event generated",
        extra={
            "event_id": event.id,
            "type": event_def["type"],
            "zone_id": zone_id,
        },
    )
    return event


async def _close_expired_events(db: AsyncSession) -> int:
    """Close events that have exceeded their duration.

    Returns:
        Number of events closed.
    """
    now = datetime.now(tz=UTC)
    closed = 0

    active_q = select(WorldEvent).where(WorldEvent.status == "active")
    result = await db.execute(active_q)

    for event in result.scalars().all():
        # Find duration for this event type
        duration_hours: int = 3  # default
        for edef in EVENT_TYPES:
            if edef["type"] == event.type:
                duration_hours = edef["duration_hours"]
                break

        expires_at = event.started_at + timedelta(hours=duration_hours)
        if now > expires_at:
            event.status = "completed"
            event.ended_at = now
            closed += 1

    if closed:
        await db.commit()
        logger.info("Closed expired events", extra={"count": closed})

    return closed


async def get_active_events_for_context(db: AsyncSession) -> list[str]:
    """Get active events formatted for tick prompt context.

    Returns:
        List of event description strings.
    """
    query = select(WorldEvent).where(WorldEvent.status == "active")
    result = await db.execute(query)

    return [f"{e.title}: {e.description}" for e in result.scalars().all() if e.title]
