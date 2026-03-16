"""Memory system for agents — read/write/format memories from agent_actions."""

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import AgentAction

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


async def get_recent_memories(
    db: AsyncSession,
    agent_id: int,
    limit: int = 10,
) -> list[str]:
    """Get agent's recent memories as formatted strings.

    Returns a list of human-readable memory strings suitable
    for inclusion in LLM prompts.
    """
    query = (
        select(AgentAction)
        .where(AgentAction.agent_id == agent_id)
        .order_by(AgentAction.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    actions = list(result.scalars().all())

    return [_format_memory(a) for a in reversed(actions)]


async def get_memories_since(
    db: AsyncSession,
    agent_id: int,
    since: datetime,
    limit: int = 20,
) -> list[str]:
    """Get memories since a specific time."""
    query = (
        select(AgentAction)
        .where(
            AgentAction.agent_id == agent_id,
            AgentAction.created_at >= since,
        )
        .order_by(AgentAction.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    actions = list(result.scalars().all())

    return [_format_memory(a) for a in reversed(actions)]


async def get_chat_context(
    db: AsyncSession,
    agent_id: int,
    hours: int = 24,
    limit: int = 15,
) -> list[str]:
    """Get memory context for chat — richer format for Pro model.

    Includes recent memories from the last N hours, formatted
    with timestamps for a more natural conversation.
    """
    since = datetime.now(tz=UTC) - timedelta(hours=hours)
    query = (
        select(AgentAction)
        .where(
            AgentAction.agent_id == agent_id,
            AgentAction.created_at >= since,
        )
        .order_by(AgentAction.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    actions = list(result.scalars().all())

    return [_format_memory_rich(a) for a in reversed(actions)]


async def record_memory(
    db: AsyncSession,
    agent_id: int,
    action_type: str,
    details: dict | None = None,
    tick_number: int | None = None,
    tokens_used: int = 0,
    model_used: str | None = None,
) -> AgentAction:
    """Record an action as a memory in the database."""
    action = AgentAction(
        agent_id=agent_id,
        action_type=action_type,
        details=details,
        tick_number=tick_number,
        tokens_used=tokens_used,
        model_used=model_used,
    )
    db.add(action)
    await db.flush()
    return action


async def get_memory_summary(
    db: AsyncSession,
    agent_id: int,
) -> dict[str, int | str]:
    """Get a summary of agent's memory stats."""
    from sqlalchemy import func

    total_q = select(func.count(AgentAction.id)).where(
        AgentAction.agent_id == agent_id,
    )
    total = (await db.execute(total_q)).scalar() or 0

    last_q = (
        select(AgentAction.created_at)
        .where(AgentAction.agent_id == agent_id)
        .order_by(AgentAction.created_at.desc())
        .limit(1)
    )
    last = (await db.execute(last_q)).scalar()

    return {
        "total_memories": total,
        "last_memory_at": str(last) if last else "never",
    }


# ── Private helpers ──────────────────────────────────────────


def _format_memory(action: AgentAction) -> str:
    """Format an action into a concise memory string for tick prompts."""
    label = _ACTION_LABELS.get(action.action_type, action.action_type)

    detail_text = ""
    if action.details:
        detail_text = _extract_detail(action.details)

    if detail_text:
        return f"{label}: {detail_text}"
    return label


def _format_memory_rich(action: AgentAction) -> str:
    """Format an action into a rich memory string for chat context."""
    label = _ACTION_LABELS.get(action.action_type, action.action_type)

    time_str = ""
    if action.created_at:
        time_str = action.created_at.strftime("%H:%M")

    detail_text = ""
    if action.details:
        detail_text = _extract_detail(action.details)

    parts = [f"[{time_str}]" if time_str else "", label]
    if detail_text:
        parts.append(f"({detail_text})")
    return " ".join(p for p in parts if p)


def _extract_detail(details: dict) -> str:
    """Extract the most relevant detail from action details JSON."""
    # Try common fields
    for key in ("content", "target", "command", "zone", "text", "result"):
        if key in details:
            val = str(details[key])
            return val[:100] if len(val) > 100 else val  # noqa: PLR2004

    # Fallback: compact JSON
    raw = json.dumps(details, ensure_ascii=False)
    return raw[:80] if len(raw) > 80 else raw  # noqa: PLR2004
