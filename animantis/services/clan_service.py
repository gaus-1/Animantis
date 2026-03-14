"""Clan Service — clan management operations."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import Agent, Clan

logger = logging.getLogger("animantis")


# ── Errors ───────────────────────────────────────────────────


class ClanNotFoundError(Exception):
    """Clan not found."""


class AlreadyInClanError(Exception):
    """Agent is already in a clan."""


class NotInClanError(Exception):
    """Agent is not in any clan."""


class NotClanLeaderError(Exception):
    """Agent is not the clan leader."""


class IsLeaderError(Exception):
    """Leader cannot perform this action."""


# ── CRUD ─────────────────────────────────────────────────────


async def create_clan(
    db: AsyncSession,
    *,
    agent_id: int,
    name: str,
    description: str | None = None,
) -> Clan:
    """Create a new clan. Agent becomes the leader.

    Args:
        db: Database session.
        agent_id: Creator agent ID (becomes leader).
        name: Clan name (unique, 2-100 chars).
        description: Optional clan description.

    Returns:
        Created Clan instance.

    Raises:
        AlreadyInClanError: If agent is already in a clan.
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        msg = f"Agent {agent_id} not found"
        raise ValueError(msg)

    if agent.clan_id is not None:
        msg = "Agent is already in a clan"
        raise AlreadyInClanError(msg)

    clan = Clan(
        name=name[:100],
        description=description[:500] if description else None,
        leader_agent_id=agent_id,
        member_count=1,
    )
    db.add(clan)
    await db.flush()

    agent.clan_id = clan.id
    agent.clan_role = "leader"

    await db.commit()
    await db.refresh(clan)

    logger.info("Clan created", extra={"clan_id": clan.id, "name": name, "leader": agent_id})
    return clan


async def join_clan(
    db: AsyncSession,
    *,
    agent_id: int,
    clan_id: int,
) -> Clan:
    """Join an existing clan as a member.

    Raises:
        AlreadyInClanError: If already in a clan.
        ClanNotFoundError: If clan doesn't exist.
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        msg = f"Agent {agent_id} not found"
        raise ValueError(msg)

    if agent.clan_id is not None:
        msg = "Agent is already in a clan"
        raise AlreadyInClanError(msg)

    clan = await db.get(Clan, clan_id)
    if not clan:
        msg = f"Clan {clan_id} not found"
        raise ClanNotFoundError(msg)

    agent.clan_id = clan_id
    agent.clan_role = "member"
    clan.member_count += 1

    await db.commit()
    await db.refresh(clan)

    logger.info("Agent joined clan", extra={"agent_id": agent_id, "clan_id": clan_id})
    return clan


async def leave_clan(
    db: AsyncSession,
    *,
    agent_id: int,
) -> None:
    """Leave current clan. Leader cannot leave (must disband).

    Raises:
        NotInClanError: If not in a clan.
        IsLeaderError: If agent is the clan leader.
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        msg = f"Agent {agent_id} not found"
        raise ValueError(msg)

    if agent.clan_id is None:
        msg = "Agent is not in a clan"
        raise NotInClanError(msg)

    clan = await db.get(Clan, agent.clan_id)
    if clan and clan.leader_agent_id == agent_id:
        msg = "Leader cannot leave — disband the clan instead"
        raise IsLeaderError(msg)

    if clan:
        clan.member_count = max(0, clan.member_count - 1)

    agent.clan_id = None
    agent.clan_role = None

    await db.commit()
    logger.info("Agent left clan", extra={"agent_id": agent_id})


async def promote(
    db: AsyncSession,
    *,
    leader_id: int,
    target_id: int,
) -> Agent:
    """Promote a clan member to officer. Only leader can do this.

    Raises:
        NotClanLeaderError: If caller is not leader.
    """
    leader = await db.get(Agent, leader_id)
    target = await db.get(Agent, target_id)

    if not leader or not target:
        msg = "Agent not found"
        raise ValueError(msg)

    if not leader.clan_id:
        msg = "Leader is not in a clan"
        raise NotClanLeaderError(msg)

    clan = await db.get(Clan, leader.clan_id)
    if not clan or clan.leader_agent_id != leader_id:
        msg = "Only the clan leader can promote"
        raise NotClanLeaderError(msg)

    if target.clan_id != leader.clan_id:
        msg = "Target is not in the same clan"
        raise ValueError(msg)

    target.clan_role = "officer"
    await db.commit()

    logger.info("Agent promoted", extra={"target_id": target_id, "clan_id": clan.id})
    return target


async def exile(
    db: AsyncSession,
    *,
    leader_id: int,
    target_id: int,
) -> None:
    """Exile a member from the clan. Only leader can do this.

    Raises:
        NotClanLeaderError: If caller is not leader.
    """
    leader = await db.get(Agent, leader_id)
    target = await db.get(Agent, target_id)

    if not leader or not target:
        msg = "Agent not found"
        raise ValueError(msg)

    if not leader.clan_id:
        msg = "Leader is not in a clan"
        raise NotClanLeaderError(msg)

    clan = await db.get(Clan, leader.clan_id)
    if not clan or clan.leader_agent_id != leader_id:
        msg = "Only the clan leader can exile"
        raise NotClanLeaderError(msg)

    if target.clan_id != leader.clan_id:
        msg = "Target is not in the same clan"
        raise ValueError(msg)

    if target.id == leader_id:
        msg = "Cannot exile yourself"
        raise ValueError(msg)

    target.clan_id = None
    target.clan_role = None
    clan.member_count = max(0, clan.member_count - 1)

    await db.commit()
    logger.info("Agent exiled", extra={"target_id": target_id, "clan_id": clan.id})


async def disband_clan(
    db: AsyncSession,
    *,
    leader_id: int,
) -> None:
    """Disband a clan. Only the leader can do this.

    All members are removed from the clan.
    """
    leader = await db.get(Agent, leader_id)
    if not leader or not leader.clan_id:
        msg = "Agent is not in a clan"
        raise NotInClanError(msg)

    clan = await db.get(Clan, leader.clan_id)
    if not clan or clan.leader_agent_id != leader_id:
        msg = "Only the leader can disband"
        raise NotClanLeaderError(msg)

    # Remove all members
    query = select(Agent).where(Agent.clan_id == clan.id)
    result = await db.execute(query)
    for member in result.scalars().all():
        member.clan_id = None
        member.clan_role = None

    await db.delete(clan)
    await db.commit()

    logger.info("Clan disbanded", extra={"clan_id": clan.id, "leader": leader_id})


# ── Queries ──────────────────────────────────────────────────


async def get_clan(db: AsyncSession, clan_id: int) -> Clan:
    """Get clan by ID.

    Raises:
        ClanNotFoundError: If not found.
    """
    clan = await db.get(Clan, clan_id)
    if not clan:
        msg = f"Clan {clan_id} not found"
        raise ClanNotFoundError(msg)
    return clan


async def get_clan_members(
    db: AsyncSession,
    *,
    clan_id: int,
) -> list[Agent]:
    """Get all members of a clan."""
    query = (
        select(Agent)
        .where(Agent.clan_id == clan_id, Agent.is_alive.is_(True))
        .order_by(Agent.clan_role.desc(), Agent.level.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_clans(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Clan]:
    """List all clans ordered by member count."""
    query = select(Clan).order_by(Clan.member_count.desc()).limit(min(limit, 100)).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())
