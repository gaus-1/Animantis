"""Bot handlers — chat and commands (/chat, /command)."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from animantis.bot.utils import (
    _get_or_create_user,
    async_session_factory,
)
from animantis.db.models import Agent, AgentAction
from animantis.llm.prompts import build_chat_prompt, sanitize_text
from animantis.llm.router import LLMError, generate_chat

logger = logging.getLogger("animantis")

router = Router(name="handlers_chat")


# ── /chat ────────────────────────────────────────────────────


@router.message(Command("chat"))
async def cmd_chat(message: Message) -> None:
    """Chat with agent via YandexGPT Pro."""
    if not message.from_user or not message.text:
        return

    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 3:  # noqa: PLR2004
        await message.answer(
            "Используйте: /chat `<id>` `<сообщение>`\nПример: /chat 1 Как дела?",
            parse_mode="Markdown",
        )
        return

    agent_id = _parse_int(parts[1])
    if agent_id is None:
        await message.answer("ID агента должен быть числом.")
        return

    agent, user = await _load_agent_for_owner(
        message,
        agent_id,
    )
    if not agent or not user:
        return

    # Send typing action
    if message.chat:
        from animantis.bot.main import get_bot as _get_bot

        await _get_bot().send_chat_action(
            chat_id=message.chat.id,
            action="typing",
        )

    # Build prompt and call LLM
    messages = build_chat_prompt(
        name=agent.name,
        personality=agent.personality,
        mood=agent.mood,
        level=agent.level,
        recent_memories=[],
        chat_history=[],
        user_message=sanitize_text(parts[2], 1000),
    )

    try:
        llm_response = await generate_chat(messages)
        await message.answer(
            f"💬 **{agent.name}:**\n\n{llm_response.text}",
            parse_mode="Markdown",
        )
    except LLMError:
        logger.exception("Chat LLM error", extra={"agent_id": agent_id})
        await message.answer("⚠️ AI временно недоступен. Попробуйте позже.")


# ── /command ─────────────────────────────────────────────────


@router.message(Command("command"))
async def cmd_command(message: Message) -> None:
    """Send command to agent."""
    if not message.from_user or not message.text:
        return

    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 3:  # noqa: PLR2004
        await message.answer(
            "Используйте: /command `<id>` `<текст команды>`\n"
            "Пример: /command 1 Иди на Арену и бросай вызов всем!",
            parse_mode="Markdown",
        )
        return

    agent_id = _parse_int(parts[1])
    if agent_id is None:
        await message.answer("ID агента должен быть числом.")
        return

    async with async_session_factory() as db:
        user = await _get_or_create_user(
            db,
            message.from_user.id,
            message.from_user.username,
        )
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if not agent:
            await message.answer(f"Агент #{agent_id} не найден.")
            return

        if agent.user_id != user.id:
            await message.answer("Вы можете командовать только своими агентами.")
            return

        if not agent.is_alive:
            await message.answer("💀 Этот агент мёртв.")
            return

        safe_command = sanitize_text(parts[2], 300)
        action = AgentAction(
            agent_id=agent_id,
            action_type="owner_command",
            details={
                "command": safe_command,
                "source": "telegram",
                "user_id": user.id,
            },
        )
        db.add(action)
        await db.commit()

    await message.answer(
        f"✅ Команда отправлена агенту **{agent.name}**:\n\n"
        f"_{safe_command}_\n\n"
        "Агент выполнит команду на следующем тике.",
        parse_mode="Markdown",
    )


# ── Private helpers ──────────────────────────────────────────


def _parse_int(raw: str) -> int | None:
    """Parse integer from string."""
    try:
        return int(raw)
    except ValueError:
        return None


async def _load_agent_for_owner(
    message: Message,
    agent_id: int,
) -> tuple[Agent | None, object]:
    """Load agent and verify ownership. Sends error replies."""
    if not message.from_user:
        return None, None

    async with async_session_factory() as db:
        user = await _get_or_create_user(
            db,
            message.from_user.id,
            message.from_user.username,
        )
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

    if not agent:
        await message.answer(f"Агент #{agent_id} не найден.")
        return None, None

    if agent.user_id != user.id:
        await message.answer("Вы можете общаться только со своими агентами.")
        return None, None

    if not agent.is_alive:
        await message.answer("💀 Этот агент мёртв и не может общаться.")
        return None, None

    return agent, user
