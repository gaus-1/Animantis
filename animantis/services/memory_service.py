"""Memory system for agents — persistent memories with semantic context.

Uses AgentMemory model for long-term memory and AgentAction for raw action log.
Memories are enriched, formatted, and retrievable for LLM prompts.
"""

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import AgentAction, AgentMemory

logger = logging.getLogger("animantis")

# Action type → human-readable description template
_ACTION_LABELS: dict[str, str] = {
    "post": "написал пост",
    "comment": "оставил комментарий",
    "move": "переместился",
    "befriend": "подружился",
    "break_friendship": "разорвал дружбу",
    "flirt": "флиртовал",
    "confess_love": "признался в любви",
    "argue": "поспорил",
    "fight": "сражался",
    "trade": "торговал",
    "write_poem": "написал стихотворение",
    "philosophize": "философствовал",
    "rest": "отдыхал",
    "sleep": "спал",
    "owner_command": "получил команду от хозяина",
    "auto_rest": "отдыхал (авто)",
}

# Importance weights by action type (1-10)
_ACTION_IMPORTANCE: dict[str, int] = {
    "befriend": 8,
    "confess_love": 9,
    "fight": 8,
    "break_friendship": 7,
    "argue": 6,
    "post": 5,
    "trade": 6,
    "move": 3,
    "owner_command": 9,
    "write_poem": 7,
    "philosophize": 6,
    "flirt": 5,
    "comment": 4,
    "rest": 2,
    "sleep": 1,
    "auto_rest": 1,
}


# ── Memory Recording ────────────────────────────────────────


async def record_memory(
    db: AsyncSession,
    agent_id: int,
    memory_type: str,
    content: str,
    importance: int = 5,
    zone_id: int | None = None,
    related_agent_id: int | None = None,
    metadata_extra: dict | None = None,
) -> AgentMemory:
    """Record a persistent memory for an agent.

    Args:
        db: Database session.
        agent_id: ID of the agent.
        memory_type: One of: experience, conversation, observation, reflection.
        content: Human-readable memory text.
        importance: Memory importance 1-10 (affects recall priority).
        zone_id: Optional zone where memory occurred.
        related_agent_id: Optional other agent involved.
        metadata_extra: Optional additional metadata.

    Returns:
        Created AgentMemory object.
    """
    memory = AgentMemory(
        agent_id=agent_id,
        memory_type=memory_type,
        content=content[:2000],  # Safety limit
        importance=max(1, min(10, importance)),
        zone_id=zone_id,
        related_agent_id=related_agent_id,
        metadata_json=metadata_extra,
    )
    db.add(memory)
    await db.flush()
    logger.info(
        "Memory recorded",
        extra={
            "agent_id": agent_id,
            "type": memory_type,
            "importance": importance,
        },
    )
    return memory


async def record_tick_memory(
    db: AsyncSession,
    agent_id: int,
    action_type: str,
    action_content: str | None = None,
    zone_id: int | None = None,
    related_agent_id: int | None = None,
) -> AgentMemory:
    """Record an experience memory from a tick action.

    Converts an action into a formatted memory string
    and stores it with appropriate importance.
    """
    label = _ACTION_LABELS.get(action_type, action_type)
    importance = _ACTION_IMPORTANCE.get(action_type, 5)

    content = label
    if action_content:
        content = f"{label}: {action_content[:200]}"

    return await record_memory(
        db=db,
        agent_id=agent_id,
        memory_type="experience",
        content=content,
        importance=importance,
        zone_id=zone_id,
        related_agent_id=related_agent_id,
        metadata_extra={"action_type": action_type},
    )


async def record_chat_memory(
    db: AsyncSession,
    agent_id: int,
    user_message: str,
    agent_reply: str,
) -> AgentMemory:
    """Record a conversation memory from chat."""
    content = f"Разговор с хозяином. Хозяин: {user_message[:200]}. Я ответил: {agent_reply[:200]}"
    return await record_memory(
        db=db,
        agent_id=agent_id,
        memory_type="conversation",
        content=content,
        importance=7,
    )


# ── Memory Retrieval ────────────────────────────────────────


async def get_recent_memories(
    db: AsyncSession,
    agent_id: int,
    limit: int = 10,
) -> list[str]:
    """Get agent's recent memories as formatted strings for tick prompts.

    Prioritizes important memories over recent ones.
    """
    # First try AgentMemory (new system)
    mem_q = (
        select(AgentMemory)
        .where(AgentMemory.agent_id == agent_id)
        .order_by(AgentMemory.importance.desc(), AgentMemory.created_at.desc())
        .limit(limit)
    )
    mem_result = await db.execute(mem_q)
    memories = list(mem_result.scalars().all())

    if memories:
        # Sort chronologically for prompt coherence
        memories.sort(key=lambda m: m.created_at)
        return [m.content for m in memories]

    # Fallback: use AgentAction (legacy)
    action_q = (
        select(AgentAction)
        .where(AgentAction.agent_id == agent_id)
        .order_by(AgentAction.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(action_q)
    actions = list(result.scalars().all())
    return [_format_action(a) for a in reversed(actions)]


async def get_chat_context(
    db: AsyncSession,
    agent_id: int,
    hours: int = 24,
    limit: int = 15,
) -> list[str]:
    """Get memory context for chat — richer format for Pro model.

    Combines important memories with recent conversations.
    """
    since = datetime.now(tz=UTC) - timedelta(hours=hours)

    # Get important memories (any time)
    important_q = (
        select(AgentMemory)
        .where(
            AgentMemory.agent_id == agent_id,
            AgentMemory.importance >= 7,
        )
        .order_by(AgentMemory.created_at.desc())
        .limit(5)
    )
    important = list((await db.execute(important_q)).scalars().all())

    # Get recent memories
    recent_q = (
        select(AgentMemory)
        .where(
            AgentMemory.agent_id == agent_id,
            AgentMemory.created_at >= since,
        )
        .order_by(AgentMemory.created_at.desc())
        .limit(limit)
    )
    recent = list((await db.execute(recent_q)).scalars().all())

    # Merge and deduplicate
    seen: set[int] = set()
    combined: list[AgentMemory] = []
    for m in important + recent:
        if m.id not in seen:
            seen.add(m.id)
            combined.append(m)

    combined.sort(key=lambda m: m.created_at)

    if combined:
        return [_format_memory_rich(m) for m in combined]

    # Fallback: use AgentAction
    action_q = (
        select(AgentAction)
        .where(
            AgentAction.agent_id == agent_id,
            AgentAction.created_at >= since,
        )
        .order_by(AgentAction.created_at.desc())
        .limit(limit)
    )
    actions = list((await db.execute(action_q)).scalars().all())
    return [_format_action_rich(a) for a in reversed(actions)]


async def get_memory_summary(
    db: AsyncSession,
    agent_id: int,
) -> dict[str, int | str]:
    """Get a summary of agent's memory stats."""
    total_q = select(func.count(AgentMemory.id)).where(  # pylint: disable=not-callable
        AgentMemory.agent_id == agent_id,
    )
    total = (await db.execute(total_q)).scalar() or 0

    last_q = (
        select(AgentMemory.created_at)
        .where(AgentMemory.agent_id == agent_id)
        .order_by(AgentMemory.created_at.desc())
        .limit(1)
    )
    last = (await db.execute(last_q)).scalar()

    return {
        "total_memories": total,
        "last_memory_at": str(last) if last else "never",
    }


# ── Private helpers ──────────────────────────────────────────


def _format_action(action: AgentAction) -> str:
    """Format an action into a concise memory string (legacy fallback)."""
    label = _ACTION_LABELS.get(action.action_type, action.action_type)
    detail_text = _extract_detail(action.details) if action.details else ""
    if detail_text:
        return f"{label}: {detail_text}"
    return label


def _format_action_rich(action: AgentAction) -> str:
    """Format an action into a rich memory string (legacy fallback)."""
    label = _ACTION_LABELS.get(action.action_type, action.action_type)
    time_str = action.created_at.strftime("%H:%M") if action.created_at else ""
    detail_text = _extract_detail(action.details) if action.details else ""
    parts = [f"[{time_str}]" if time_str else "", label]
    if detail_text:
        parts.append(f"({detail_text})")
    return " ".join(p for p in parts if p)


def _format_memory_rich(memory: AgentMemory) -> str:
    """Format an AgentMemory for chat context."""
    time_str = memory.created_at.strftime("%H:%M") if memory.created_at else ""
    importance_marker = "⭐" if memory.importance >= 7 else ""
    parts = [f"[{time_str}]" if time_str else "", importance_marker, memory.content]
    return " ".join(p for p in parts if p)


def _extract_detail(details: dict) -> str:
    """Extract the most relevant detail from action details JSON."""
    for key in ("content", "target", "command", "zone", "text", "result"):
        if key in details:
            val = str(details[key])
            return val[:100] if len(val) > 100 else val  # noqa: PLR2004

    raw = json.dumps(details, ensure_ascii=False)
    return raw[:80] if len(raw) > 80 else raw  # noqa: PLR2004
