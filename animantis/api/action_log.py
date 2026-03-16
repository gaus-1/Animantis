"""API routes for agent action log and stats."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.api.deps import rate_limit_api
from animantis.db.connection import get_db
from animantis.services.action_log_service import get_agent_log, get_agent_stats

router = APIRouter(
    prefix="/api/v1/log",
    tags=["log"],
    dependencies=[Depends(rate_limit_api)],
)
DbSession = Annotated[AsyncSession, Depends(get_db)]


class ActionResponse(BaseModel):
    """Action log entry."""

    id: int
    agent_id: int
    action_type: str
    details: dict[str, Any] | None
    tick_number: int | None
    tokens_used: int
    model_used: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentStatsResponse(BaseModel):
    """Aggregated agent stats."""

    total_actions: int
    total_tokens: int
    favorite_action: str | None
    favorite_action_count: int


@router.get("/{agent_id}", response_model=list[ActionResponse])
async def get_action_log(
    agent_id: int,
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
    action_type: str | None = None,
) -> list[ActionResponse]:
    """Get action history for an agent."""
    actions = await get_agent_log(
        db,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
        action_type=action_type,
    )
    return [ActionResponse.model_validate(a) for a in actions]


@router.get("/{agent_id}/stats", response_model=AgentStatsResponse)
async def get_stats(agent_id: int, db: DbSession) -> AgentStatsResponse:
    """Get aggregated stats for an agent."""
    stats = await get_agent_stats(db, agent_id=agent_id)
    return AgentStatsResponse(**stats)
