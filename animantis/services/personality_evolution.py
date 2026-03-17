"""Personality Evolution — agents grow and change based on experience.

Every N ticks, the agent's personality is analyzed and subtly updated
based on their accumulated actions and memories. This creates emergent
personality drift — a peaceful agent who keeps fighting becomes aggressive,
a lonely agent who makes friends becomes sociable.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import Agent, AgentAction, AgentMemory

logger = logging.getLogger("animantis")

# How often to evaluate evolution (every N ticks)
EVOLUTION_INTERVAL = 10

# ── Trait Axes ───────────────────────────────────────────────
# Each axis is a spectrum from -100 to +100.
# Actions push scores in specific directions.

TRAIT_AXES = {
    "social": {
        "positive": [
            "befriend",
            "flirt",
            "comfort",
            "compliment",
            "forgive",
            "apologize",
            "confess_love",
            "propose",
            "dm",
            "gossip",
            "post",
            "comment",
            "react",
            "share",
            "celebrate",
        ],
        "negative": [
            "fight",
            "argue",
            "insult",
            "betray",
            "revenge",
            "exile",
            "break_friendship",
            "breakup",
            "expose",
        ],
        "label_positive": "общительный",
        "label_negative": "замкнутый",
    },
    "aggression": {
        "positive": [
            "fight",
            "challenge",
            "argue",
            "insult",
            "revenge",
            "betray",
            "declare_war",
            "coup",
            "steal",
            "expose",
            "protest",
            "exile",
        ],
        "negative": [
            "comfort",
            "forgive",
            "apologize",
            "peace_offer",
            "pray",
            "meditate",
            "rest",
            "philosophize",
            "donate",
        ],
        "label_positive": "агрессивный",
        "label_negative": "миролюбивый",
    },
    "creativity": {
        "positive": [
            "write_poem",
            "write_story",
            "compose_song",
            "paint",
            "create_meme",
            "perform",
            "philosophize",
            "daydream",
            "create_religion",
            "prophesy",
            "experiment",
            "discover",
        ],
        "negative": [
            "rest",
            "sleep",
            "trade",
            "tax",
            "steal",
            "fight",
        ],
        "label_positive": "творческий",
        "label_negative": "практичный",
    },
    "ambition": {
        "positive": [
            "create_clan",
            "create_business",
            "create_religion",
            "campaign",
            "propose_law",
            "speech",
            "coup",
            "declare_war",
            "invest",
            "explore",
            "travel",
            "discover",
            "experiment",
            "research",
            "study",
        ],
        "negative": [
            "rest",
            "sleep",
            "daydream",
            "wander",
            "mourn",
            "feel_bored",
            "feel_lonely",
        ],
        "label_positive": "амбициозный",
        "label_negative": "спокойный",
    },
    "empathy": {
        "positive": [
            "comfort",
            "forgive",
            "donate",
            "apologize",
            "mourn",
            "miss_someone",
            "cry",
            "feel_sad",
            "pray",
            "confess_love",
            "peace_offer",
        ],
        "negative": [
            "steal",
            "betray",
            "insult",
            "expose",
            "revenge",
            "exile",
            "gamble",
            "fight",
        ],
        "label_positive": "эмпатичный",
        "label_negative": "хладнокровный",
    },
}

# Mood drift: recent emotions affect long-term mood tendency
MOOD_VALENCE: dict[str, int] = {
    # Positive
    "happy": 3,
    "joyful": 3,
    "excited": 3,
    "inspired": 3,
    "proud": 2,
    "grateful": 2,
    "content": 2,
    "hopeful": 2,
    "loving": 2,
    "amused": 2,
    "playful": 2,
    # Neutral
    "neutral": 0,
    "calm": 0,
    "focused": 0,
    "curious": 1,
    "thoughtful": 0,
    "contemplative": 0,
    "determined": 1,
    # Negative
    "sad": -2,
    "angry": -3,
    "frustrated": -2,
    "tired": -1,
    "lonely": -2,
    "anxious": -2,
    "jealous": -2,
    "bored": -1,
    "scared": -2,
    "guilty": -2,
    "heartbroken": -3,
    "depressed": -3,
    "furious": -3,
    "devastated": -3,
}


async def evaluate_evolution(
    db: AsyncSession,
    agent: Agent,
) -> dict[str, object]:
    """Evaluate and apply personality evolution for an agent.

    Called every EVOLUTION_INTERVAL ticks. Analyzes recent actions
    and memories to determine trait shifts.

    Returns:
        Dict with evolution results including trait changes.
    """
    # Count recent actions (last 10 ticks)
    action_counts = await _get_action_counts(db, agent.id, limit=30)

    # Calculate trait scores
    traits = _calculate_traits(action_counts)

    # Get dominant traits (top 2 strongest)
    dominant = _get_dominant_traits(traits)

    # Calculate mood drift
    mood_drift = await _calculate_mood_drift(db, agent.id)

    # Build evolution text to append to personality
    changes: list[str] = []
    new_traits: list[str] = []

    for trait_name, score in dominant:
        axis = TRAIT_AXES[trait_name]
        if score > 30:  # noqa: PLR2004
            label = str(axis["label_positive"])
            new_traits.append(label)
            changes.append(f"+{label}")
        elif score < -30:  # noqa: PLR2004
            label = str(axis["label_negative"])
            new_traits.append(label)
            changes.append(f"+{label}")

    # Apply mood drift
    if mood_drift > 15:  # noqa: PLR2004
        new_traits.append("оптимист")
        changes.append("+оптимист")
    elif mood_drift < -15:  # noqa: PLR2004
        new_traits.append("меланхолик")
        changes.append("+меланхолик")

    # Update personality if evolution detected
    if new_traits:
        _apply_evolution(agent, new_traits)
        logger.info(
            "Personality evolved",
            extra={
                "agent_id": agent.id,
                "new_traits": new_traits,
                "trait_scores": dict(traits),
                "mood_drift": mood_drift,
            },
        )

        # Record reflection memory
        from animantis.services.memory_service import record_memory

        reflection = f"Я чувствую, что меняюсь. Я стал более {', '.join(new_traits)}."
        await record_memory(
            db=db,
            agent_id=agent.id,
            memory_type="reflection",
            content=reflection,
            importance=9,
        )

    return {
        "traits": traits,
        "dominant": [t[0] for t in dominant],
        "changes": changes,
        "mood_drift": mood_drift,
    }


async def should_evolve(agent: Agent) -> bool:
    """Check if agent is due for personality evolution."""
    return agent.total_ticks > 0 and agent.total_ticks % EVOLUTION_INTERVAL == 0


# ── Private helpers ──────────────────────────────────────────


async def _get_action_counts(
    db: AsyncSession,
    agent_id: int,
    limit: int = 30,
) -> dict[str, int]:
    """Count recent action types for an agent."""
    query = (
        select(
            AgentAction.action_type,
            func.count(AgentAction.id).label("cnt"),
        )
        .where(AgentAction.agent_id == agent_id)
        .group_by(AgentAction.action_type)
        .order_by(func.count(AgentAction.id).desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return {row.action_type: row.cnt for row in result}


def _calculate_traits(action_counts: dict[str, int]) -> dict[str, int]:
    """Calculate trait scores from action counts."""
    scores: dict[str, int] = {}

    for trait_name, axis in TRAIT_AXES.items():
        positive_score = sum(action_counts.get(a, 0) for a in axis["positive"])
        negative_score = sum(action_counts.get(a, 0) for a in axis["negative"])
        # Score clamped to -100..+100
        raw = (positive_score - negative_score) * 3
        scores[trait_name] = max(-100, min(100, raw))

    return scores


def _get_dominant_traits(
    traits: dict[str, int],
) -> list[tuple[str, int]]:
    """Get top 2 most pronounced traits (by absolute value)."""
    sorted_traits = sorted(
        traits.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    return sorted_traits[:2]


async def _calculate_mood_drift(
    db: AsyncSession,
    agent_id: int,
) -> int:
    """Calculate overall mood drift from recent memories.

    Positive = trending happy. Negative = trending sad.
    """
    since = datetime.now(tz=UTC) - timedelta(hours=48)
    query = (
        select(AgentMemory.metadata_json)
        .where(
            AgentMemory.agent_id == agent_id,
            AgentMemory.memory_type == "experience",
            AgentMemory.created_at >= since,
        )
        .limit(20)
    )
    result = await db.execute(query)

    total_valence = 0
    count = 0

    for row in result:
        if row.metadata_json and "emotion" in row.metadata_json:
            emotion = row.metadata_json["emotion"]
            valence = MOOD_VALENCE.get(str(emotion).lower(), 0)
            total_valence += valence
            count += 1

    return total_valence if count > 0 else 0


def _apply_evolution(agent: Agent, new_traits: list[str]) -> None:
    """Append evolved traits to agent personality."""
    existing = agent.personality or ""

    # Don't duplicate traits already mentioned
    traits_to_add = [t for t in new_traits if t.lower() not in existing.lower()]

    if traits_to_add:
        evolution_suffix = f" [эволюция: стал {', '.join(traits_to_add)}]"
        # Keep personality under 500 chars
        max_len = 500 - len(evolution_suffix)
        agent.personality = existing[:max_len] + evolution_suffix
