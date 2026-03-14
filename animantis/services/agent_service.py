"""Agent Service — CRUD operations for agents."""

import logging
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import Agent, User

logger = logging.getLogger("animantis")


# ── Errors ───────────────────────────────────────────────────


class AgentLimitError(Exception):
    """User has reached max agents."""


class AgentNotFoundError(Exception):
    """Agent not found."""


class NotOwnerError(Exception):
    """User is not the owner of this agent."""


# ── CRUD ─────────────────────────────────────────────────────


async def create_agent(
    db: AsyncSession,
    *,
    user_id: int,
    name: str,
    personality: str,
    backstory: str | None = None,
    avatar_type: str | None = None,
    max_agents: int = 5,
) -> Agent:
    """Create a new agent for a user.

    Args:
        db: Database session.
        user_id: Owner user ID.
        name: Agent name (1-100 chars).
        personality: Agent personality (1-500 chars).
        backstory: Optional backstory (up to 1000 chars).
        avatar_type: Optional avatar type.
        max_agents: Maximum agents per user.

    Returns:
        Created Agent instance.

    Raises:
        AgentLimitError: If user has too many agents.
    """
    # Check agent count
    count_query = select(Agent).where(
        Agent.user_id == user_id,
        Agent.is_alive.is_(True),
    )
    result = await db.execute(count_query)
    alive_count = len(result.scalars().all())

    if alive_count >= max_agents:
        msg = f"Max {max_agents} alive agents allowed"
        raise AgentLimitError(msg)

    # Create agent
    agent = Agent(
        user_id=user_id,
        name=name[:100],
        personality=personality[:500],
        backstory=backstory[:1000] if backstory else None,
        avatar_type=avatar_type,
        zone_id=1,  # Central Square (start zone)
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    logger.info("Agent created", extra={"agent_id": agent.id, "name": name})
    return agent


async def get_agent(db: AsyncSession, agent_id: int) -> Agent:
    """Get agent by ID.

    Raises:
        AgentNotFoundError: If not found.
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        msg = f"Agent {agent_id} not found"
        raise AgentNotFoundError(msg)
    return agent


async def get_user_agents(db: AsyncSession, user_id: int) -> list[Agent]:
    """Get all agents belonging to a user."""
    query = select(Agent).where(Agent.user_id == user_id).order_by(Agent.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def verify_ownership(db: AsyncSession, agent_id: int, user_id: int) -> Agent:
    """Get agent and verify ownership.

    Raises:
        AgentNotFoundError: If not found.
        NotOwnerError: If user doesn't own agent.
    """
    agent = await get_agent(db, agent_id)
    if agent.user_id != user_id:
        msg = "Not the owner"
        raise NotOwnerError(msg)
    return agent


async def kill_agent(db: AsyncSession, agent_id: int, user_id: int) -> Agent:
    """Kill (deactivate) an agent.

    Raises:
        AgentNotFoundError: If not found.
        NotOwnerError: If user doesn't own agent.
    """
    from datetime import datetime

    agent = await verify_ownership(db, agent_id, user_id)
    agent.is_alive = False
    agent.is_active = False
    agent.died_at = datetime.now(tz=UTC)
    await db.commit()

    logger.info("Agent killed", extra={"agent_id": agent_id})
    return agent


async def get_or_create_user(db: AsyncSession, telegram_id: int, username: str | None) -> User:
    """Get existing user or create new one by telegram_id."""
    query = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user:
        # Update username if changed
        if username and user.username != username:
            user.username = username
            await db.commit()
        return user

    # Create new user
    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("User created", extra={"user_id": user.id, "telegram_id": telegram_id})
    return user
