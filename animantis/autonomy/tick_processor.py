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
from animantis.services.memory_service import get_recent_memories

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
        owner_command=None,  # Phase 6: Telegram bot commands
    )

    cache_key = f"tick:{agent_id}:{agent.zone_id}:{len(nearby_agents)}"
    llm_response = await generate_tick(messages, cache_key=cache_key)

    # 5. Parse LLM response
    action_data = _parse_action(llm_response.text)
    action_type = action_data.get("action", "rest")

    # 6. Apply effects
    energy_delta = get_energy_cost(action_type)
    xp_delta = get_xp_reward(action_type)

    agent.energy = max(0, min(100, agent.energy + energy_delta))
    agent.xp += xp_delta
    agent.level = _calculate_level(agent.xp)
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
