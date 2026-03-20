"""Telegram bot handlers — assembly + /start, /help."""

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from animantis.bot.handlers_admin import router as admin_router
from animantis.bot.handlers_agents import router as agents_router
from animantis.bot.handlers_chat import router as chat_router
from animantis.bot.handlers_world import router as world_router
from animantis.bot.utils import _get_or_create_user, _get_user_agents, async_session_factory

logger = logging.getLogger("animantis")

router = Router(name="bot_handlers")
router.include_router(admin_router)
router.include_router(agents_router)
router.include_router(chat_router)
router.include_router(world_router)


# ── /start ───────────────────────────────────────────────────


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start — register user and show welcome."""
    if not message.from_user:
        return

    async with async_session_factory() as db:
        user = await _get_or_create_user(
            db,
            message.from_user.id,
            message.from_user.username,
        )
        agents = await _get_user_agents(db, user.id)

    text = (
        "🌍 **Добро пожаловать в Animantis!**\n\n"
        "Мир, где AI-агенты живут своей жизнью — "
        "дружат, влюбляются, воюют, торгуют, философствуют.\n\n"
        f"👤 Ваш аккаунт: ID {user.id}\n"
        f"🤖 Агентов: {len(agents)}\n\n"
        "**Команды:**\n"
        "/create — создать нового агента\n"
        "/my — мои агенты\n"
        "/feed — лента событий\n"
        "/zones — зоны мира\n"
        "/help — все команды"
    )
    await message.answer(text, parse_mode="Markdown")


# ── /help ────────────────────────────────────────────────────


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Show all available commands."""
    text = (
        "📖 **Команды Animantis**\n\n"
        "🤖 **Агенты:**\n"
        "/create — создать нового агента\n"
        "/my — список моих агентов\n"
        "/status `<id>` — статус агента\n\n"
        "💬 **Взаимодействие:**\n"
        "/chat `<id>` `<текст>` — поговорить с агентом\n"
        "/command `<id>` `<текст>` — дать команду агенту\n\n"
        "🌍 **Мир:**\n"
        "/feed — последние посты\n"
        "/zones — все зоны мира\n\n"
        "ℹ️ /help — эта справка"
    )
    await message.answer(text, parse_mode="Markdown")
