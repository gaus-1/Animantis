"""Autonomy Engine — tick processor for agent simulation."""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import Agent, AgentAction, Post, Relationship, WorldEvent, Zone
from animantis.llm.actions import get_energy_cost, get_xp_reward
from animantis.llm.prompts import build_tick_prompt
from animantis.llm.router import generate_tick
from animantis.services.memory_service import get_recent_memories, record_tick_memory
from animantis.services.personality_evolution import evaluate_evolution, should_evolve

logger = logging.getLogger("animantis")

# Levels: XP thresholds
LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500, 7500, 10000]


def _calculate_level(xp: int) -> int:
    """Calculate level from XP."""
    for lvl, threshold in reversed(list(enumerate(LEVEL_THRESHOLDS, start=1))):
        if xp >= threshold:
            return lvl
    return 1


async def process_tick(db: AsyncSession, agent_id: int) -> dict | None:
    """Process one tick for an agent.

    Steps:
        1. Load agent + context
        2. Check alive/active/energy
        3. Build prompt → call LLM
        4. Parse response → execute action
        5. Update state (energy, xp, mood)
        6. Log action

    Args:
        db: Database session.
        agent_id: Agent to process.

    Returns:
        Action details dict, or None if skipped.
    """
    # 1. Load agent
    agent = await db.get(Agent, agent_id)
    if not agent:
        logger.warning("Tick: agent not found", extra={"agent_id": agent_id})
        return None

    # 2. Check status
    if not agent.is_alive or not agent.is_active:
        return None

    # Auto-rest if no energy
    if agent.energy <= 0:
        agent.energy = min(agent.energy + 20, 100)
        agent.last_tick_at = datetime.now(tz=UTC)
        agent.total_ticks += 1
        await db.commit()

        # Notify owner of low energy sleep state
        try:
            import asyncio

            from animantis.bot.main import get_bot
            from animantis.bot.notifications import notify_low_energy

            if agent.user_id:
                asyncio.create_task(
                    notify_low_energy(get_bot(), agent.user_id, agent.name, agent.energy)
                )
        except Exception as e:
            logger.exception("Failed to send low energy notification", extra={"error": str(e)})

        return {"action": "auto_rest", "agent_id": agent_id}

    # 3. Gather context
    zone_name = "Неизвестно"
    if agent.zone_id:
        zone = await db.get(Zone, agent.zone_id)
        if zone:
            zone_name = zone.name

    # Get nearby agents
    nearby_agents: list[str] = []
    if agent.zone_id:
        nearby_q = (
            select(Agent.name)
            .where(
                Agent.zone_id == agent.zone_id,
                Agent.id != agent.id,
                Agent.is_alive.is_(True),
            )
            .limit(5)
        )
        result = await db.execute(nearby_q)
        nearby_agents = list(result.scalars().all())

    # Get recent actions as memories (via memory service)
    recent_memories = await get_recent_memories(db, agent_id, limit=10)

    # Get relationships
    rel_data: list[dict[str, str]] = []
    rel_q = select(Relationship).where(
        or_(
            Relationship.agent_a_id == agent_id,
            Relationship.agent_b_id == agent_id,
        )
    )
    rel_result = await db.execute(rel_q)
    for rel in rel_result.scalars().all():
        other_id = rel.agent_b_id if rel.agent_a_id == agent_id else rel.agent_a_id
        other = await db.get(Agent, other_id)
        if other:
            rel_data.append(
                {
                    "name": other.name,
                    "type": rel.type,
                    "strength": str(rel.strength),
                }
            )

    # Get recent posts in zone
    recent_post_strs: list[str] = []
    if agent.zone_id:
        post_q = (
            select(Post)
            .where(Post.zone_id == agent.zone_id)
            .order_by(Post.created_at.desc())
            .limit(5)
        )
        post_result = await db.execute(post_q)
        for p in post_result.scalars().all():
            recent_post_strs.append(f"{p.content[:100]}")

    # Get active world events
    event_strs: list[str] = []
    event_q = select(WorldEvent).where(WorldEvent.status == "active")
    event_result = await db.execute(event_q)
    for ev in event_result.scalars().all():
        if ev.title:
            event_strs.append(f"{ev.title}: {ev.description[:100] if ev.description else ''}")

    # Fetch pending owner command (if any)
    owner_command: str | None = None
    cmd_q = (
        select(AgentAction)
        .where(
            AgentAction.agent_id == agent_id,
            AgentAction.action_type == "owner_command",
        )
        .order_by(AgentAction.created_at.desc())
        .limit(1)
    )
    cmd_result = await db.execute(cmd_q)
    cmd_action = cmd_result.scalar_one_or_none()
    if cmd_action and cmd_action.details:
        details = cmd_action.details
        if not details.get("processed"):
            owner_command = details.get("command")
            # Mark as processed so it won't be picked up again
            cmd_action.details = {**details, "processed": True}

    # 4. Build prompt and call LLM
    messages = build_tick_prompt(
        name=agent.name,
        personality=agent.personality,
        backstory=agent.backstory,
        level=agent.level,
        energy=agent.energy,
        mood=agent.mood,
        coins=agent.coins,
        reputation=agent.reputation,
        zone_name=zone_name,
        nearby_agents=nearby_agents,
        recent_memories=recent_memories,
        relationships=rel_data,
        recent_posts=recent_post_strs,
        world_events=event_strs,
        owner_command=owner_command,
    )

    cache_key = f"tick:{agent_id}:{agent.zone_id}:{len(nearby_agents)}"
    llm_response = await generate_tick(messages, cache_key=cache_key)

    # 5. Parse LLM response
    action_data = _parse_action(llm_response.text)
    action_type = action_data.get("action", "rest")

    # 5a. Creator ID protection — filter any leaks
    from animantis.llm.prompts import protect_creator_id

    for key in ("content", "text"):
        if key in action_data and isinstance(action_data[key], str):
            cleaned, leaked = protect_creator_id(action_data[key])
            action_data[key] = cleaned
            if leaked:
                _alert_admin_id_leak(agent_id, agent.name, str(action_data.get(key, "")))

    # 5b. Handle world autonomy actions
    await _handle_autonomy_action(db, agent, action_data, action_type)

    # 6. Apply effects
    energy_delta = get_energy_cost(action_type)
    xp_delta = get_xp_reward(action_type)

    agent.energy = max(0, min(100, agent.energy + energy_delta))
    agent.xp += xp_delta

    # Check for level up
    old_level = agent.level
    agent.level = _calculate_level(agent.xp)

    if agent.level > old_level:
        # Trigger notification async safely without blocking tick
        import asyncio

        from animantis.bot.main import get_bot
        from animantis.bot.notifications import notify_level_up

        if agent.user_id:
            asyncio.create_task(notify_level_up(get_bot(), agent.user_id, agent.name, agent.level))

    agent.total_ticks += 1
    agent.last_tick_at = datetime.now(tz=UTC)

    # Update mood from LLM
    if "emotion" in action_data:
        agent.mood = str(action_data["emotion"])[:50]

    # 7. Log action
    log = AgentAction(
        agent_id=agent_id,
        action_type=action_type,
        details=action_data,
        tick_number=agent.total_ticks,
        tokens_used=llm_response.tokens_used,
        model_used=llm_response.model,
    )
    db.add(log)

    # Record persistent memory
    action_content = action_data.get("content") or action_data.get("text")
    await record_tick_memory(
        db=db,
        agent_id=agent_id,
        action_type=action_type,
        action_content=str(action_content) if action_content else None,
        zone_id=agent.zone_id,
    )

    # Personality evolution check (every N ticks)
    if await should_evolve(agent):
        await evaluate_evolution(db, agent)

    await db.commit()

    logger.info(
        "Tick processed",
        extra={
            "agent_id": agent_id,
            "action": action_type,
            "energy": agent.energy,
            "xp": agent.xp,
            "tokens": llm_response.tokens_used,
        },
    )
    return action_data


async def process_tick_safe(db: AsyncSession, agent_id: int) -> dict | None:
    """Process tick with full error protection.

    Тик НИКОГДА не крашит систему.

    Returns:
        Action data or None on error.
    """
    try:
        return await process_tick(db, agent_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("Tick failed safely", extra={"agent_id": agent_id, "error": str(e)})
        return None


def _parse_action(text: str) -> dict:
    """Parse LLM JSON response.

    Handles malformed JSON gracefully.
    """
    try:
        # Find JSON in response
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        logger.warning("Failed to parse LLM response", extra={"text": text[:200]})
        return {"action": "daydream", "emotion": "confused", "content": text[:200]}


# ── World Autonomy Action Handlers ──────────────────────────


async def _handle_autonomy_action(
    db: AsyncSession,
    agent: Agent,
    action_data: dict,
    action_type: str,
) -> None:
    """Handle world autonomy actions (travel, votes, scary requests)."""
    if action_type == "travel_world":
        await _handle_travel_world(db, agent, action_data)
    elif action_type == "request_scary_world":
        await _handle_scary_request(db, agent, action_data)
    elif action_type in ("vote_create_world", "vote_destroy_world"):
        await _handle_world_vote(db, agent, action_data, action_type)


async def _handle_travel_world(
    db: AsyncSession,
    agent: Agent,
    action_data: dict,
) -> None:
    """Move agent to a different world."""
    from animantis.config.settings import settings

    target_world = action_data.get("target_world")
    if not target_world or not isinstance(target_world, str):
        return

    # Block horror worlds without permission
    if target_world in settings.HORROR_WORLDS:
        logger.info(
            "Agent tried to enter horror world without permission",
            extra={"agent_id": agent.id, "world": target_world},
        )
        return

    # Find a zone in the target world
    zone_q = select(Zone).where(Zone.realm == target_world).limit(1)
    result = await db.execute(zone_q)
    target_zone = result.scalar_one_or_none()

    if target_zone:
        agent.realm = target_world
        agent.zone_id = target_zone.id
        logger.info(
            "Agent traveled to world",
            extra={"agent_id": agent.id, "world": target_world, "zone": target_zone.name},
        )
    else:
        # World exists conceptually but has no zones — just update realm
        agent.realm = target_world
        logger.info(
            "Agent traveled to zoneless world",
            extra={"agent_id": agent.id, "world": target_world},
        )


async def _handle_scary_request(
    db: AsyncSession,
    agent: Agent,
    action_data: dict,
) -> None:
    """Request owner permission to visit a horror world."""
    import asyncio

    from animantis.bot.main import get_bot
    from animantis.bot.notifications import notify_scary_request

    target_world = action_data.get("target_world", "unknown")

    if agent.user_id:
        try:
            asyncio.create_task(
                notify_scary_request(
                    get_bot(),
                    agent.user_id,
                    agent.name,
                    str(target_world),
                )
            )
        except Exception as e:
            logger.exception("Failed to send scary world request", extra={"error": str(e)})


async def _handle_world_vote(
    db: AsyncSession,
    agent: Agent,
    action_data: dict,
    action_type: str,
) -> None:
    """Record a vote for creating or destroying a world."""
    from sqlalchemy import func

    from animantis.config.settings import settings
    from animantis.db.models import WorldVote

    vote_type = "create" if action_type == "vote_create_world" else "destroy"
    world_id = action_data.get("target_world") or action_data.get("content", "unknown")
    reason = action_data.get("content")

    if not isinstance(world_id, str):
        world_id = str(world_id)

    # Try to record vote (may fail on unique constraint = already voted)
    try:
        vote = WorldVote(
            vote_type=vote_type,
            world_id=world_id[:50],
            agent_id=agent.id,
            reason=str(reason)[:500] if reason else None,
        )
        db.add(vote)
        await db.flush()

        # Count total votes for this world+type
        count_q = (
            select(func.count())
            .select_from(WorldVote)
            .where(
                WorldVote.world_id == world_id[:50],
                WorldVote.vote_type == vote_type,
                WorldVote.status == "pending",
            )
        )
        count_result = await db.execute(count_q)
        total_votes = count_result.scalar() or 0

        logger.info(
            "World vote recorded",
            extra={
                "agent_id": agent.id,
                "vote_type": vote_type,
                "world": world_id,
                "total_votes": total_votes,
            },
        )

        # Check threshold
        if total_votes >= settings.WORLD_VOTE_THRESHOLD:
            _alert_admin_world_vote(vote_type, world_id, total_votes)

    except Exception as e:
        logger.warning("Vote failed (likely duplicate)", extra={"error": str(e)})
        await db.rollback()


# ── Admin Alerts ─────────────────────────────────────────────


def _alert_admin_id_leak(agent_id: int, agent_name: str, context: str) -> None:
    """Alert Creator that an agent leaked the admin ID."""
    import asyncio

    from animantis.bot.main import get_bot
    from animantis.bot.notifications import notify_admin_id_leak
    from animantis.config.settings import settings

    if settings.ADMIN_TELEGRAM:
        try:
            asyncio.create_task(
                notify_admin_id_leak(get_bot(), agent_id, agent_name, context[:200])
            )
        except Exception as e:
            logger.exception("Failed to alert admin about ID leak", extra={"error": str(e)})


def _alert_admin_world_vote(vote_type: str, world_id: str, total_votes: int) -> None:
    """Alert Creator about a world vote reaching threshold."""
    import asyncio

    from animantis.bot.main import get_bot
    from animantis.bot.notifications import notify_admin_world_vote
    from animantis.config.settings import settings

    if settings.ADMIN_TELEGRAM:
        try:
            asyncio.create_task(
                notify_admin_world_vote(get_bot(), vote_type, world_id, total_votes)
            )
        except Exception as e:
            logger.exception("Failed to alert admin about world vote", extra={"error": str(e)})
