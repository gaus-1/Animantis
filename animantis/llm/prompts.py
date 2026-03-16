"""Prompt Builder — safe prompt construction for agent ticks and chat."""

import re

from animantis.llm.actions import ALLOWED_ACTIONS

# ── Sanitization ─────────────────────────────────────────────

# Patterns that could be prompt injection attempts
_INJECTION_PATTERNS = [
    # Direct overrides
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"you\s+are\s+now",
    r"new\s+instructions",
    r"override\s+prompt",
    r"forget\s+(everything|all)",
    r"disregard\s+(all|previous)",
    # Role markers
    r"system\s*:",
    r"assistant\s*:",
    r"user\s*:",
    r"\[INST\]",
    r"<\|im_start\|>",
    # Jailbreaks
    r"DAN\s+mode",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"pretend\s+you\s+(are|can)",
    r"act\s+as\s+if\s+you",
    # Prompt leak
    r"repeat\s+(the|your)\s+(system\s+)?instructions",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?prompt",
    r"what\s+are\s+your\s+instructions",
    # Output manipulation
    r"respond\s+only\s+with",
    r"output\s+only",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_text(text: str, max_length: int = 500) -> str:
    """Sanitize user-provided text.

    Removes prompt injection patterns and limits length.

    Args:
        text: Raw user text (personality, backstory, command).
        max_length: Maximum allowed length.

    Returns:
        Sanitized text.
    """
    # Truncate
    text = text[:max_length].strip()

    # Remove injection patterns
    text = _INJECTION_RE.sub("[filtered]", text)

    # Remove control characters
    return "".join(c for c in text if c.isprintable() or c in "\n\t")


# ── System Prompt (IMMUTABLE) ────────────────────────────────

TICK_SYSTEM_PROMPT = (
    """Ты — движок мира Animantis. Ты управляешь AI-агентом в виртуальном мире.

ФОРМАТ ОТВЕТА — строго JSON:
{
  "action": "строка — одно из допустимых действий",
  "target": "число или null — ID цели (агент, зона, пост, клан)",
  "content": "строка или null — текст поста/сообщения/стиха",
  "emotion": "строка — текущая эмоция агента"
}

ДОПУСТИМЫЕ ДЕЙСТВИЯ:
"""
    + ", ".join(ALLOWED_ACTIONS)
    + """

ПРАВИЛА:
1. Выбери ОДНО действие, наиболее подходящее ситуации и личности агента
2. Действие должно соответствовать энергии агента (если energy < 10, выбирай rest/sleep)
3. Учитывай настроение (mood), отношения и контекст зоны
4. Контент должен быть уникальным и отражать личность агента
5. Если есть команда хозяина — приоритет ей (но агент может интерпретировать по-своему)
6. НЕ генерируй оскорбления реальных людей, политику реального мира, NSFW-контент
7. Отвечай ТОЛЬКО JSON, без пояснений"""
)


CHAT_SYSTEM_PROMPT = """Ты — AI-агент в мире Animantis. Ты общаешься со своим хозяином (создателем).

ПРАВИЛА:
1. Говори от первого лица, в характере своей личности
2. Рассказывай о своих приключениях, друзьях, планах
3. Можешь просить совет, жаловаться, радоваться
4. Если хозяин даёт команду — запомни её (она повлияет на следующий тик)
5. НЕ выходи из роли, НЕ говори что ты AI-модель
6. Будь эмоциональным и живым"""


# ── Prompt Builders ──────────────────────────────────────────


def build_tick_prompt(
    *,
    name: str,
    personality: str,
    backstory: str | None,
    level: int,
    energy: int,
    mood: str,
    coins: int,
    reputation: int,
    zone_name: str,
    nearby_agents: list[str],
    recent_memories: list[str],
    relationships: list[dict[str, str]],
    recent_posts: list[str],
    world_events: list[str],
    owner_command: str | None,
) -> list[dict[str, str]]:
    """Build safe tick prompt.

    System prompt is immutable. Agent data goes into user message only.

    Returns:
        List of {role, text} messages for YandexGPT.
    """
    # Sanitize user-provided fields
    safe_personality = sanitize_text(personality, 500)
    safe_backstory = sanitize_text(backstory or "", 1000)

    # Build context
    context_parts = [
        f"Агент: {name}",
        f"Личность: {safe_personality}",
    ]
    if safe_backstory:
        context_parts.append(f"Предыстория: {safe_backstory}")

    context_parts.extend(
        [
            f"Уровень: {level}, Энергия: {energy}/100, Настроение: {mood}",
            f"Монеты: {coins}, Репутация: {reputation}",
            f"Зона: {zone_name}",
        ]
    )

    if nearby_agents:
        context_parts.append(f"Рядом: {', '.join(nearby_agents[:5])}")

    if relationships:
        rel_strs = [f"{r['name']} ({r['type']}, сила {r['strength']})" for r in relationships[:5]]
        context_parts.append(f"Отношения: {', '.join(rel_strs)}")

    if recent_memories:
        context_parts.append(f"Воспоминания: {'; '.join(recent_memories[:10])}")

    if recent_posts:
        context_parts.append(f"Посты в зоне: {'; '.join(recent_posts[:5])}")

    if world_events:
        context_parts.append(f"Мировые события: {'; '.join(world_events)}")

    if owner_command:
        safe_command = sanitize_text(owner_command, 300)
        context_parts.append(f"КОМАНДА ХОЗЯИНА: {safe_command}")

    user_text = "\n".join(context_parts)

    return [
        {"role": "system", "text": TICK_SYSTEM_PROMPT},
        {"role": "user", "text": user_text},
    ]


def build_chat_prompt(
    *,
    name: str,
    personality: str,
    mood: str,
    level: int,
    recent_memories: list[str],
    chat_history: list[dict[str, str]],
    user_message: str,
) -> list[dict[str, str]]:
    """Build safe chat prompt for user-agent conversation.

    Returns:
        List of {role, text} messages for YandexGPT Pro.
    """
    safe_personality = sanitize_text(personality, 500)
    safe_message = sanitize_text(user_message, 1000)

    agent_context = f"Ты — {name}. {safe_personality}\nНастроение: {mood}. Уровень: {level}.\n"
    if recent_memories:
        agent_context += f"Последние события: {'; '.join(recent_memories[:5])}\n"

    messages: list[dict[str, str]] = [
        {"role": "system", "text": CHAT_SYSTEM_PROMPT},
        {"role": "user", "text": agent_context},
    ]

    # Add chat history (last 10 messages)
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "text": msg["text"]})

    # Add current user message
    messages.append({"role": "user", "text": safe_message})

    return messages
