"""Bot handlers — world info (/feed, /zones)."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from animantis.bot.utils import async_session_factory
from animantis.db.models import Agent, Post, Zone

logger = logging.getLogger("animantis")

router = Router(name="handlers_world")


# ── /feed ────────────────────────────────────────────────────


@router.message(Command("feed"))
async def cmd_feed(message: Message) -> None:
    """Show latest posts from the global feed."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Post).order_by(Post.created_at.desc()).limit(10),
        )
        posts = result.scalars().all()

    if not posts:
        await message.answer(
            "📭 Лента пуста. Создайте агента — он начнёт писать!",
        )
        return

    lines = ["📰 **Последние посты:**\n"]
    for post in posts:
        author_name = await _get_author_name(post.author_agent_id)
        preview = _content_preview(post.content)
        lines.append(f"**{author_name}:** {preview}")
        lines.append(f"  ❤️ {post.likes} | {post.post_type}")
        lines.append("")

    await message.answer("\n".join(lines), parse_mode="Markdown")


# ── /zones ───────────────────────────────────────────────────


@router.message(Command("zones"))
async def cmd_zones(message: Message) -> None:
    """Show all world zones."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Zone).order_by(Zone.realm, Zone.id),
        )
        zones = result.scalars().all()

    if not zones:
        await message.answer("Зоны не найдены.")
        return

    planet = [z for z in zones if z.realm == "planet"]
    cosmic = [z for z in zones if z.realm == "cosmic"]

    lines = ["🌍 **Зоны мира Animantis:**\n", "**Планета:**"]
    for z in planet:
        lines.append(f"  📍 {z.name} ({z.category or ''})")

    if cosmic:
        lines.append("\n**Космос:**")
        for z in cosmic:
            lines.append(f"  🚀 {z.name} ({z.category or ''})")

    await message.answer("\n".join(lines), parse_mode="Markdown")


# ── Private helpers ──────────────────────────────────────────


async def _get_author_name(agent_id: int) -> str:
    """Get agent name by ID for feed display."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(Agent.name).where(Agent.id == agent_id),
        )
        return result.scalar_one_or_none() or "Неизвестный"


def _content_preview(text: str, limit: int = 100) -> str:
    """Truncate text for preview."""
    return (text[:limit] + "...") if len(text) > limit else text
