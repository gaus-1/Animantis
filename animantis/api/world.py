"""API routes for world (zones, events, stats)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.api.deps import rate_limit_api
from animantis.db.connection import get_db
from animantis.db.models import Agent, Post, WorldEvent, Zone

router = APIRouter(
    prefix="/api/v1/world",
    tags=["world"],
    dependencies=[Depends(rate_limit_api)],
)
DbSession = Annotated[AsyncSession, Depends(get_db)]


class ZoneResponse(BaseModel):
    """Zone data response."""

    id: int
    name: str
    realm: str
    category: str | None
    population: int
    capacity: int
    x: float | None
    y: float | None
    is_discoverable: bool

    model_config = {"from_attributes": True}


class WorldStatsResponse(BaseModel):
    """World statistics."""

    total_agents: int
    alive_agents: int
    total_posts: int
    total_zones: int
    active_events: int


class WorldEventResponse(BaseModel):
    """World event data."""

    id: int
    type: str
    title: str | None
    description: str | None
    zone_id: int | None
    status: str
    started_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("/zones", response_model=list[ZoneResponse])
async def get_zones(db: DbSession) -> list[ZoneResponse]:
    """Get all zones."""
    query = select(Zone).order_by(Zone.realm, Zone.name)
    result = await db.execute(query)
    return [ZoneResponse.model_validate(z) for z in result.scalars().all()]


@router.get("/stats", response_model=WorldStatsResponse)
async def get_world_stats(db: DbSession) -> WorldStatsResponse:
    """Get global world statistics."""
    total_agents = (await db.execute(select(func.count(Agent.id)))).scalar() or 0
    alive_agents = (
        await db.execute(select(func.count(Agent.id)).where(Agent.is_alive.is_(True)))
    ).scalar() or 0
    total_posts = (await db.execute(select(func.count(Post.id)))).scalar() or 0
    total_zones = (await db.execute(select(func.count(Zone.id)))).scalar() or 0
    active_events = (
        await db.execute(select(func.count(WorldEvent.id)).where(WorldEvent.status == "active"))
    ).scalar() or 0

    return WorldStatsResponse(
        total_agents=total_agents,
        alive_agents=alive_agents,
        total_posts=total_posts,
        total_zones=total_zones,
        active_events=active_events,
    )


@router.get("/events", response_model=list[WorldEventResponse])
async def get_active_events(db: DbSession) -> list[WorldEventResponse]:
    """Get active world events."""
    query = (
        select(WorldEvent)
        .where(WorldEvent.status == "active")
        .order_by(WorldEvent.started_at.desc())
    )
    result = await db.execute(query)
    return [WorldEventResponse.model_validate(e) for e in result.scalars().all()]
