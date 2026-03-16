"""Telegram notification service — push events to users.

Sends notifications about agent events via Telegram bot.
Events: level up, death, clan invite, relationship changes, world events.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger("animantis")


# ── Event messages ───────────────────────────────────────────


def _level_up_msg(agent_name: str, level: int) -> str:
    return f"🎉 *{agent_name}* достиг уровня *{level}*!"


def _death_msg(agent_name: str) -> str:
    return f"☠️ *{agent_name}* погиб... Покойся с миром."


def _low_energy_msg(agent_name: str, energy: int) -> str:
    return f"⚡ *{agent_name}* устал (энергия: {energy}). Пора отдохнуть!"


def _relationship_msg(agent_name: str, target: str, rel_type: str) -> str:
    icons = {
        "friend": "🤝",
        "enemy": "⚔️",
        "lover": "💕",
        "rival": "😤",
        "mentor": "📖",
    }
    icon = icons.get(rel_type, "🔹")
    return f"{icon} *{agent_name}* теперь {rel_type} с *{target}*"


def _world_event_msg(event_name: str, description: str) -> str:
    return f"🌍 *Мировое событие:* {event_name}\n{description}"


def _clan_invite_msg(agent_name: str, clan_name: str) -> str:
    return f"⚔️ *{agent_name}* приглашён в клан *{clan_name}*!"


# ── Send notification ────────────────────────────────────────


async def send_notification(
    bot: Bot,
    chat_id: int,
    text: str,
) -> bool:
    """Send a notification message to a Telegram user.

    Args:
        bot: aiogram Bot instance.
        chat_id: Telegram chat ID of the user.
        text: Markdown-formatted message.

    Returns:
        True if sent successfully, False otherwise.
    """
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
        )
        return True
    except TelegramAPIError as e:
        logger.warning("Failed to send notification to %d: %s", chat_id, e)
        return False


# ── High-level notifiers ────────────────────────────────────


async def notify_level_up(
    bot: Bot,
    chat_id: int,
    agent_name: str,
    level: int,
) -> bool:
    """Notify user that their agent leveled up."""
    return await send_notification(bot, chat_id, _level_up_msg(agent_name, level))


async def notify_death(
    bot: Bot,
    chat_id: int,
    agent_name: str,
) -> bool:
    """Notify user that their agent died."""
    return await send_notification(bot, chat_id, _death_msg(agent_name))


async def notify_low_energy(
    bot: Bot,
    chat_id: int,
    agent_name: str,
    energy: int,
) -> bool:
    """Notify user when agent energy is critically low."""
    return await send_notification(
        bot,
        chat_id,
        _low_energy_msg(agent_name, energy),
    )


async def notify_relationship(
    bot: Bot,
    chat_id: int,
    agent_name: str,
    target_name: str,
    rel_type: str,
) -> bool:
    """Notify user about a new relationship."""
    return await send_notification(
        bot,
        chat_id,
        _relationship_msg(agent_name, target_name, rel_type),
    )


async def notify_world_event(
    bot: Bot,
    chat_id: int,
    event_name: str,
    description: str,
) -> bool:
    """Notify user about a world event."""
    return await send_notification(
        bot,
        chat_id,
        _world_event_msg(event_name, description),
    )


async def notify_clan_invite(
    bot: Bot,
    chat_id: int,
    agent_name: str,
    clan_name: str,
) -> bool:
    """Notify user about a clan invitation."""
    return await send_notification(
        bot,
        chat_id,
        _clan_invite_msg(agent_name, clan_name),
    )
