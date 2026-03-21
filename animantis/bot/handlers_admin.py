"""Telegram admin handlers — Creator control panel.

Only accessible by ADMIN_TELEGRAM. Full god-mode control over agents and worlds.
"""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from animantis.bot.utils import async_session_factory
from animantis.config.settings import settings
from animantis.db.models import AdminAction, Agent, WorldVote

logger = logging.getLogger("animantis")

router = Router(name="admin_handlers")


# ── Access check ─────────────────────────────────────────────


def _is_admin(message: Message) -> bool:
    """Check if the message sender is the Creator."""
    if not message.from_user:
        return False
    return message.from_user.id == settings.ADMIN_TELEGRAM


async def _log_admin_action(
    action_type: str,
    target_agent_id: int | None = None,
    target_world: str | None = None,
    details: dict | None = None,
) -> None:
    """Log an admin action to the database."""
    async with async_session_factory() as db:
        log = AdminAction(
            action_type=action_type,
            target_agent_id=target_agent_id,
            target_world=target_world,
            details=details,
        )
        db.add(log)
        await db.commit()


# ── /admin — Main panel ─────────────────────────────────────


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Show admin control panel."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    async with async_session_factory() as db:
        # Count agents
        agent_count = await db.scalar(select(func.count()).select_from(Agent))
        alive_count = await db.scalar(
            select(func.count()).select_from(Agent).where(Agent.is_alive.is_(True))
        )
        # Count pending votes
        pending_votes = await db.scalar(
            select(func.count()).select_from(WorldVote).where(WorldVote.status == "pending")
        )

    text = (
        "👑 *Панель Создателя*\n\n"
        f"🤖 Агентов: {agent_count} (живых: {alive_count})\n"
        f"🗳 Голосов (ожидание): {pending_votes}\n\n"
        "**Команды:**\n"
        "/agents — список всех агентов\n"
        "/kill `<agent_id>` — уничтожить агента\n"
        "/ban\\_agent `<agent_id>` — забанить навсегда\n"
        "/promote `<agent_id>` `<role>` — назначить роль\n"
        "/demote `<agent_id>` — снять с должности\n"
        "/destroy\\_world `<world_id>` — уничтожить мир\n"
        "/approve\\_world `<world_id>` — одобрить создание мира\n"
        "/reject\\_world `<world_id>` — отклонить создание мира\n"
        "/worlds\\_stats — статистика миров"
    )
    await message.answer(text, parse_mode="Markdown")


# ── /agents — List all agents ────────────────────────────────


@router.message(Command("agents"))
async def cmd_agents(message: Message) -> None:
    """List all agents with their IDs."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    async with async_session_factory() as db:
        result = await db.execute(select(Agent).order_by(Agent.id).limit(50))
        agents = list(result.scalars().all())

    if not agents:
        await message.answer("🤖 Нет агентов в системе.")
        return

    lines = ["👑 *Все агенты:*\n"]
    for a in agents:
        status = "✅" if a.is_alive else "☠️"
        active = "🟢" if a.is_active else "🔴"
        lines.append(
            f"{status}{active} ID:{a.id} *{a.name}* Lv{a.level} 🌍{a.realm} Owner:{a.user_id}"
        )

    await message.answer("\n".join(lines), parse_mode="Markdown")


# ── /kill — Destroy agent ────────────────────────────────────


@router.message(Command("kill"))
async def cmd_kill(message: Message) -> None:
    """Kill (destroy) an agent permanently."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer("Использование: /kill `<agent_id>`", parse_mode="Markdown")
        return

    try:
        agent_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID агента.")
        return

    async with async_session_factory() as db:
        agent = await db.get(Agent, agent_id)
        if not agent:
            await message.answer(f"❌ Агент ID {agent_id} не найден.")
            return

        agent.is_alive = False
        agent.is_active = False
        await db.commit()

    await _log_admin_action("kill", target_agent_id=agent_id)
    await message.answer(
        f"☠️ Агент *{agent.name}* (ID:{agent_id}) уничтожен Создателем.", parse_mode="Markdown"
    )


# ── /ban_agent — Permanent ban ───────────────────────────────


@router.message(Command("ban_agent"))
async def cmd_ban_agent(message: Message) -> None:
    """Permanently ban an agent (kill + deactivate)."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer("Использование: /ban\\_agent `<agent_id>`", parse_mode="Markdown")
        return

    try:
        agent_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID агента.")
        return

    async with async_session_factory() as db:
        agent = await db.get(Agent, agent_id)
        if not agent:
            await message.answer(f"❌ Агент ID {agent_id} не найден.")
            return

        agent.is_alive = False
        agent.is_active = False
        agent.reputation = -999
        await db.commit()

    await _log_admin_action("ban", target_agent_id=agent_id)
    await message.answer(
        f"🔨 Агент *{agent.name}* (ID:{agent_id}) забанен навсегда.",
        parse_mode="Markdown",
    )


# ── /promote — Assign role ───────────────────────────────────


@router.message(Command("promote"))
async def cmd_promote(message: Message) -> None:
    """Promote an agent to a world role."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = (message.text or "").split()
    if len(args) < 3:
        await message.answer(
            "Использование: /promote `<agent_id>` `<role>`\n"
            "Роли: governor, judge, general, minister, advisor",
            parse_mode="Markdown",
        )
        return

    try:
        agent_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID агента.")
        return

    role = args[2]

    async with async_session_factory() as db:
        agent = await db.get(Agent, agent_id)
        if not agent:
            await message.answer(f"❌ Агент ID {agent_id} не найден.")
            return

        agent.clan_role = role
        await db.commit()

    await _log_admin_action("promote", target_agent_id=agent_id, details={"role": role})
    await message.answer(
        f"👑 Агент *{agent.name}* (ID:{agent_id}) назначен: *{role}*",
        parse_mode="Markdown",
    )


# ── /demote — Remove role ────────────────────────────────────


@router.message(Command("demote"))
async def cmd_demote(message: Message) -> None:
    """Remove an agent's role."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer("Использование: /demote `<agent_id>`", parse_mode="Markdown")
        return

    try:
        agent_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID агента.")
        return

    async with async_session_factory() as db:
        agent = await db.get(Agent, agent_id)
        if not agent:
            await message.answer(f"❌ Агент ID {agent_id} не найден.")
            return

        old_role = agent.clan_role
        agent.clan_role = None
        await db.commit()

    await _log_admin_action("demote", target_agent_id=agent_id, details={"old_role": old_role})
    await message.answer(
        f"📉 Агент *{agent.name}* (ID:{agent_id}) снят с должности.",
        parse_mode="Markdown",
    )


# ── /destroy_world — Destroy a world ─────────────────────────


@router.message(Command("destroy_world"))
async def cmd_destroy_world(message: Message) -> None:
    """Destroy a world — all agents there moved to neural_nexus."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer("Использование: /destroy\\_world `<world_id>`", parse_mode="Markdown")
        return

    world_id = args[1]

    async with async_session_factory() as db:
        # Move all agents from this world to neural_nexus
        result = await db.execute(select(Agent).where(Agent.realm == world_id))
        affected = list(result.scalars().all())

        for agent in affected:
            agent.realm = "neural_nexus"
            agent.zone_id = None

        await db.commit()

    await _log_admin_action(
        "destroy_world", target_world=world_id, details={"agents_moved": len(affected)}
    )
    await message.answer(
        f"💥 Мир *{world_id}* уничтожен Создателем.\n"
        f"🤖 {len(affected)} агентов перемещены в Neural Nexus.",
        parse_mode="Markdown",
    )


# ── /approve_world — Approve world creation ──────────────────


@router.message(Command("approve_world"))
async def cmd_approve_world(message: Message) -> None:
    """Approve a world creation/destruction vote."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer("Использование: /approve\\_world `<world_id>`", parse_mode="Markdown")
        return

    world_id = args[1]

    async with async_session_factory() as db:
        result = await db.execute(
            select(WorldVote).where(
                WorldVote.world_id == world_id,
                WorldVote.status == "pending",
            )
        )
        votes = list(result.scalars().all())

        for v in votes:
            v.status = "approved"

        await db.commit()

    await _log_admin_action("approve_world", target_world=world_id, details={"votes": len(votes)})
    await message.answer(
        f"✅ Мир *{world_id}* одобрен Создателем ({len(votes)} голосов).",
        parse_mode="Markdown",
    )


# ── /reject_world — Reject world vote ────────────────────────


@router.message(Command("reject_world"))
async def cmd_reject_world(message: Message) -> None:
    """Reject a world creation/destruction vote."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer("Использование: /reject\\_world `<world_id>`", parse_mode="Markdown")
        return

    world_id = args[1]

    async with async_session_factory() as db:
        result = await db.execute(
            select(WorldVote).where(
                WorldVote.world_id == world_id,
                WorldVote.status == "pending",
            )
        )
        votes = list(result.scalars().all())

        for v in votes:
            v.status = "rejected"

        await db.commit()

    await _log_admin_action("reject_world", target_world=world_id, details={"votes": len(votes)})
    await message.answer(
        f"❌ Мир *{world_id}* отклонён Создателем ({len(votes)} голосов).",
        parse_mode="Markdown",
    )


# ── /worlds_stats — World population stats ───────────────────


@router.message(Command("worlds_stats"))
async def cmd_worlds_stats(message: Message) -> None:
    """Show agent population by world."""
    if not _is_admin(message):
        await message.answer("⛔ Доступ запрещён.")
        return

    async with async_session_factory() as db:
        result = await db.execute(
            select(
                Agent.realm,
                func.count().label("count"),
            )
            .where(Agent.is_alive.is_(True))
            .group_by(Agent.realm)
            .order_by(func.count().desc())
        )
        rows = result.all()

    if not rows:
        await message.answer("📊 Нет живых агентов.")
        return

    lines = ["📊 *Население миров:*\n"]
    for realm, count in rows:
        lines.append(f"🌍 *{realm}*: {count} агентов")

    await message.answer("\n".join(lines), parse_mode="Markdown")
