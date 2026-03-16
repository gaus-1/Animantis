"""Relationship Service — social bonds between agents."""

import logging

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import Relationship

logger = logging.getLogger("animantis")

RELATIONSHIP_TYPES = [
    "friend",
    "best_friend",
    "enemy",
    "rival",
    "lover",
    "ex_lover",
    "mentor",
    "student",
    "ally",
    "business_partner",
]


async def create_or_update_relationship(
    db: AsyncSession,
    *,
    agent_a_id: int,
    agent_b_id: int,
    rel_type: str,
    strength: int = 50,
) -> Relationship:
    """Create or update a relationship between two agents."""
    if rel_type not in RELATIONSHIP_TYPES:
        msg = f"Invalid relationship type: {rel_type}"
        raise ValueError(msg)

    a_id, b_id = min(agent_a_id, agent_b_id), max(agent_a_id, agent_b_id)

    query = select(Relationship).where(
        Relationship.agent_a_id == a_id,
        Relationship.agent_b_id == b_id,
        Relationship.type == rel_type,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        existing.strength = max(0, min(100, strength))
        await db.commit()
        return existing

    rel = Relationship(
        agent_a_id=a_id,
        agent_b_id=b_id,
        type=rel_type,
        strength=max(0, min(100, strength)),
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    
    # Notify both owners
    try:
        from animantis.db.models import Agent
        from animantis.bot.notifications import notify_relationship
        import asyncio
        
        agent_a = await db.get(Agent, a_id)
        agent_b = await db.get(Agent, b_id)
        
        if agent_a and agent_b:
            if agent_a.user_id:
                asyncio.create_task(notify_relationship(agent_a.user_id, agent_a.name, agent_b.name, rel.type, "new"))
            if agent_b.user_id:
                asyncio.create_task(notify_relationship(agent_b.user_id, agent_b.name, agent_a.name, rel.type, "new"))
    except Exception as e:
        logger.exception("Failed to send relationship notification", extra={"error": str(e)})

    return rel


async def get_agent_relationships(
    db: AsyncSession,
    *,
    agent_id: int,
) -> list[Relationship]:
    """Get all relationships for an agent."""
    query = select(Relationship).where(
        or_(
            Relationship.agent_a_id == agent_id,
            Relationship.agent_b_id == agent_id,
        )
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def remove_relationship(
    db: AsyncSession,
    *,
    agent_a_id: int,
    agent_b_id: int,
    rel_type: str,
) -> bool:
    """Remove a specific relationship."""
    a_id, b_id = min(agent_a_id, agent_b_id), max(agent_a_id, agent_b_id)
    query = select(Relationship).where(
        Relationship.agent_a_id == a_id,
        Relationship.agent_b_id == b_id,
        Relationship.type == rel_type,
    )
    result = await db.execute(query)
    rel = result.scalar_one_or_none()

    if rel:
        await db.delete(rel)
        await db.commit()
        return True
    return False
