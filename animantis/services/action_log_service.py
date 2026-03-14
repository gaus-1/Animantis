"""Action Log Service — history of agent actions."""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import AgentAction

logger = logging.getLogger("animantis")


async def get_agent_log(
    db: AsyncSession,
    *,
    agent_id: int,
    limit: int = 50,
    offset: int = 0,
    action_type: str | None = None,
) -> list[AgentAction]:
    """Get action history for an agent."""
    query = (
        select(AgentAction)
        .where(AgentAction.agent_id == agent_id)
        .order_by(AgentAction.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    if action_type:
        query = query.where(AgentAction.action_type == action_type)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_agent_stats(
    db: AsyncSession,
    *,
    agent_id: int,
) -> dict:
    """Get aggregated stats for an agent."""
    tokens_q = select(func.sum(AgentAction.tokens_used)).where(AgentAction.agent_id == agent_id)
    total_tokens = (await db.execute(tokens_q)).scalar() or 0

    count_q = select(func.count(AgentAction.id)).where(AgentAction.agent_id == agent_id)
    total_actions = (await db.execute(count_q)).scalar() or 0

    top_action_q = (
        select(AgentAction.action_type, func.count(AgentAction.id).label("cnt"))
        .where(AgentAction.agent_id == agent_id)
        .group_by(AgentAction.action_type)
        .order_by(func.count(AgentAction.id).desc())
        .limit(1)
    )
    top_row = (await db.execute(top_action_q)).first()

    return {
        "total_actions": total_actions,
        "total_tokens": total_tokens,
        "favorite_action": top_row[0] if top_row else None,
        "favorite_action_count": top_row[1] if top_row else 0,
    }
