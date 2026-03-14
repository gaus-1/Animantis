"""Celery app and Beat schedule for Animantis Autonomy Engine."""

import logging

from celery import Celery  # type: ignore[import-untyped]

from animantis.config.settings import settings

logger = logging.getLogger("animantis")

# ── Celery App ───────────────────────────────────────────────

celery_app = Celery(
    "animantis",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=4,
    task_soft_time_limit=60,
    task_time_limit=120,
)


# ── Tasks ────────────────────────────────────────────────────


@celery_app.task(name="animantis.tick_batch")
def tick_batch(plan: str = "free") -> dict:
    """Process ticks for all agents of a given plan.

    Args:
        plan: User plan tier (free, pro, ultra).

    Returns:
        Summary of processed ticks.
    """
    import asyncio

    return asyncio.get_event_loop().run_until_complete(_tick_batch_async(plan))


async def _tick_batch_async(plan: str) -> dict:
    """Async implementation of tick batch processing."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from animantis.autonomy.tick_processor import process_tick_safe
    from animantis.db.models import Agent, User

    engine = create_async_engine(settings.DATABASE_URL, pool_size=5)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    processed = 0
    errors = 0

    async with session_factory() as db:
        # Get all active agents for this plan tier
        query = (
            select(Agent)
            .join(User, Agent.user_id == User.id)
            .where(
                Agent.is_alive.is_(True),
                Agent.is_active.is_(True),
                User.plan == plan,
            )
        )
        result = await db.execute(query)
        agents = list(result.scalars().all())

        for agent in agents:
            try:
                await process_tick_safe(db, agent.id)
                processed += 1
            except Exception as e:  # noqa: BLE001
                errors += 1
                logger.exception("Tick batch error", extra={"agent_id": agent.id, "error": str(e)})

    await engine.dispose()

    logger.info(
        "Tick batch completed",
        extra={"plan": plan, "processed": processed, "errors": errors},
    )
    return {"plan": plan, "processed": processed, "errors": errors}


@celery_app.task(name="animantis.generate_world_event")
def generate_world_event_task() -> dict:
    """Generate a random world event."""
    import asyncio

    return asyncio.get_event_loop().run_until_complete(_generate_event_async())


async def _generate_event_async() -> dict:
    """Async implementation for world event generation."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from animantis.autonomy.world_events import generate_world_event

    engine = create_async_engine(settings.DATABASE_URL, pool_size=2)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        event = await generate_world_event(db)

    await engine.dispose()

    if event:
        return {"event_id": event.id, "type": event.type, "title": event.title}
    return {"skipped": True}


# ── Beat Schedule ────────────────────────────────────────────

celery_app.conf.beat_schedule = {
    "tick-free": {
        "task": "animantis.tick_batch",
        "schedule": 3600,  # every hour
        "args": ("free",),
    },
    "tick-pro": {
        "task": "animantis.tick_batch",
        "schedule": 600,  # every 10 minutes
        "args": ("pro",),
    },
    "tick-ultra": {
        "task": "animantis.tick_batch",
        "schedule": 60,  # every minute
        "args": ("ultra",),
    },
    "world-events": {
        "task": "animantis.generate_world_event",
        "schedule": 3600,  # every hour
    },
}
