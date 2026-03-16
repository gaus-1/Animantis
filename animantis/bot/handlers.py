"""Telegram bot handlers — all /commands and callbacks."""

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.bot.keyboards import (
    agent_actions_keyboard,
    agents_list_keyboard,
    avatar_type_keyboard,
    confirm_keyboard,
)
from animantis.bot.states import AgentCreation
from animantis.db.connection import async_session as async_session_factory
from animantis.db.models import Agent, AgentAction, Post, User, Zone
from animantis.llm.prompts import build_chat_prompt, sanitize_text
from animantis.llm.router import LLMError, generate_chat

logger = logging.getLogger("animantis")

router = Router(name="bot_handlers")


# ── Helpers ──────────────────────────────────────────────────


async def _get_or_create_user(db: AsyncSession, telegram_id: int, username: str | None) -> User:
    """Get existing user or create a new one."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        # Update username if changed
        if username and user.username != username:
            user.username = username
            await db.commit()
        return user

    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _get_user_agents(db: AsyncSession, user_id: int) -> list[Agent]:
    """Get all agents for a user."""
    result = await db.execute(
        select(Agent)
        .where(Agent.user_id == user_id, Agent.is_alive.is_(True))
        .order_by(Agent.created_at.desc())
    )
    return list(result.scalars().all())


# ── /start ───────────────────────────────────────────────────


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start — register user and show welcome."""
    if not message.from_user:
        return

    async with async_session_factory() as db:
        user = await _get_or_create_user(db, message.from_user.id, message.from_user.username)
        agents = await _get_user_agents(db, user.id)

    agent_count = len(agents)
    text = (
        "🌍 **Добро пожаловать в Animantis!**\n\n"
        "Мир, где AI-агенты живут своей жизнью — "
        "дружат, влюбляются, воюют, торгуют, философствуют.\n\n"
        f"👤 Ваш аккаунт: ID {user.id}\n"
        f"🤖 Агентов: {agent_count}\n\n"
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


# ── /create (FSM) ────────────────────────────────────────────


@router.message(Command("create"))
async def cmd_create(message: Message, state: FSMContext) -> None:
    """Start agent creation — step 1: name."""
    if not message.from_user:
        return

    async with async_session_factory() as db:
        user = await _get_or_create_user(db, message.from_user.id, message.from_user.username)
        agents = await _get_user_agents(db, user.id)

    if len(agents) >= 5:  # noqa: PLR2004
        await message.answer("⚠️ Максимум 5 агентов. Удалите одного, чтобы создать нового.")
        return

    await state.update_data(user_db_id=user.id)
    await state.set_state(AgentCreation.name)
    await message.answer(
        "🤖 **Создание агента — Шаг 1/4**\n\nКак зовут вашего агента?\n_(до 100 символов)_",
        parse_mode="Markdown",
    )


@router.message(AgentCreation.name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Process agent name — step 2: personality."""
    if not message.text:
        await message.answer("Введите текстовое имя.")
        return

    name = message.text.strip()[:100]
    if len(name) < 1:
        await message.answer("Имя не может быть пустым.")
        return

    await state.update_data(name=name)
    await state.set_state(AgentCreation.personality)
    await message.answer(
        f"✅ Имя: **{name}**\n\n"
        "🧠 **Шаг 2/4 — Личность**\n\n"
        "Опишите характер, привычки, ценности агента.\n"
        "_(10-500 символов)_\n\n"
        "_Пример: «Дерзкая, умная, немного циничная. "
        "Обожает поэзию и ненавидит ложь.»_",
        parse_mode="Markdown",
    )


@router.message(AgentCreation.personality)
async def process_personality(message: Message, state: FSMContext) -> None:
    """Process personality — step 3: backstory."""
    if not message.text:
        await message.answer("Введите текстовое описание.")
        return

    personality = message.text.strip()[:500]
    if len(personality) < 10:  # noqa: PLR2004
        await message.answer("Описание слишком короткое (минимум 10 символов).")
        return

    await state.update_data(personality=personality)
    await state.set_state(AgentCreation.avatar_type)
    await message.answer(
        "📖 **Шаг 3/4 — Аватар**\n\nВыберите тип аватара:",
        parse_mode="Markdown",
        reply_markup=avatar_type_keyboard(),
    )


@router.callback_query(F.data.startswith("avatar:"))
async def process_avatar(callback: CallbackQuery, state: FSMContext) -> None:
    """Process avatar selection — step 4: confirm."""
    if not callback.data or not callback.message:
        return

    avatar = callback.data.split(":")[1]
    if avatar == "skip":
        await state.update_data(avatar_type=None)
    else:
        await state.update_data(avatar_type=avatar)

    data = await state.get_data()
    avatar_display = avatar if avatar != "skip" else "—"

    await callback.message.edit_text(  # type: ignore[union-attr]
        "📋 **Шаг 4/4 — Подтверждение**\n\n"
        f"**Имя:** {data['name']}\n"
        f"**Личность:** {data['personality'][:100]}...\n"
        f"**Аватар:** {avatar_display}\n\n"
        "Создать агента?",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard(),
    )
    await state.set_state(AgentCreation.confirmation)
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:"))
async def process_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Process creation confirmation."""
    if not callback.data or not callback.message:
        return

    choice = callback.data.split(":")[1]

    if choice != "yes":
        await callback.message.edit_text("❌ Создание отменено.")  # type: ignore[union-attr]
        await state.clear()
        await callback.answer()
        return

    data = await state.get_data()

    async with async_session_factory() as db:
        agent = Agent(
            user_id=data["user_db_id"],
            name=data["name"],
            personality=data["personality"],
            avatar_type=data.get("avatar_type"),
            zone_id=1,  # Центральная площадь
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)

    await state.clear()
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"🎉 **Агент «{agent.name}» создан!**\n\n"
        f"📍 Зона: Центральная площадь\n"
        f"⚡ Энергия: {agent.energy}/100\n"
        f"💰 Монеты: {agent.coins}\n"
        f"🆔 ID: {agent.id}\n\n"
        "Ваш агент начнёт жить автономно на следующем тике!\n"
        f"Используйте /status {agent.id} чтобы следить за ним.",
        parse_mode="Markdown",
    )
    await callback.answer("Агент создан! 🎉")


# ── /my ──────────────────────────────────────────────────────


@router.message(Command("my"))
async def cmd_my(message: Message) -> None:
    """Show user's agents."""
    if not message.from_user:
        return

    async with async_session_factory() as db:
        user = await _get_or_create_user(db, message.from_user.id, message.from_user.username)
        agents = await _get_user_agents(db, user.id)

    if not agents:
        await message.answer("У вас пока нет агентов.\nСоздайте первого: /create")
        return

    agents_data: list[dict[str, int | str]] = [
        {"id": a.id, "name": a.name, "level": a.level} for a in agents
    ]
    await message.answer(
        f"🤖 **Ваши агенты ({len(agents)}):**",
        parse_mode="Markdown",
        reply_markup=agents_list_keyboard(agents_data),
    )


# ── /status ──────────────────────────────────────────────────


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Show agent status by ID."""
    if not message.from_user or not message.text:
        return

    parts = message.text.strip().split()
    if len(parts) < 2:  # noqa: PLR2004
        await message.answer("Используйте: /status `<id агента>`", parse_mode="Markdown")
        return

    try:
        agent_id = int(parts[1])
    except ValueError:
        await message.answer("ID агента должен быть числом.")
        return

    async with async_session_factory() as db:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

    if not agent:
        await message.answer(f"Агент #{agent_id} не найден.")
        return

    # Get zone name
    zone_name = "Неизвестно"
    if agent.zone_id:
        async with async_session_factory() as db:
            result = await db.execute(select(Zone).where(Zone.id == agent.zone_id))
            zone = result.scalar_one_or_none()
            if zone:
                zone_name = zone.name

    alive_emoji = "💚" if agent.is_alive else "💀"
    mood_map = {
        "neutral": "😐",
        "happy": "😊",
        "sad": "😢",
        "angry": "😠",
        "inspired": "✨",
        "anxious": "😰",
        "proud": "😤",
        "bored": "😴",
    }
    mood_emoji = mood_map.get(agent.mood, "🤔")

    text = (
        f"{alive_emoji} **{agent.name}**\n\n"
        f"📊 Уровень: {agent.level} (XP: {agent.xp})\n"
        f"⚡ Энергия: {agent.energy}/100\n"
        f"{mood_emoji} Настроение: {agent.mood}\n"
        f"💰 Монеты: {agent.coins}\n"
        f"⭐ Репутация: {agent.reputation}\n"
        f"🏛 Влияние: {agent.influence}\n"
        f"📍 Зона: {zone_name}\n"
        f"🔄 Всего тиков: {agent.total_ticks}"
    )
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=agent_actions_keyboard(agent.id),
    )


# ── Callback: agent_status ───────────────────────────────────


@router.callback_query(F.data.startswith("agent_status:"))
async def callback_agent_status(callback: CallbackQuery) -> None:
    """Handle inline button press for agent status."""
    if not callback.data or not callback.message:
        return

    agent_id = int(callback.data.split(":")[1])

    async with async_session_factory() as db:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

    if not agent:
        await callback.answer("Агент не найден", show_alert=True)
        return

    zone_name = "Неизвестно"
    if agent.zone_id:
        async with async_session_factory() as db:
            result = await db.execute(select(Zone).where(Zone.id == agent.zone_id))
            zone = result.scalar_one_or_none()
            if zone:
                zone_name = zone.name

    alive_emoji = "💚" if agent.is_alive else "💀"
    text = (
        f"{alive_emoji} **{agent.name}**\n\n"
        f"📊 Lv.{agent.level} | ⚡ {agent.energy}/100 | 💰 {agent.coins}\n"
        f"😌 {agent.mood} | ⭐ {agent.reputation}\n"
        f"📍 {zone_name} | 🔄 {agent.total_ticks} тиков"
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        parse_mode="Markdown",
        reply_markup=agent_actions_keyboard(agent.id),
    )
    await callback.answer()


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

    try:
        agent_id = int(parts[1])
    except ValueError:
        await message.answer("ID агента должен быть числом.")
        return

    user_message = parts[2]

    async with async_session_factory() as db:
        user = await _get_or_create_user(db, message.from_user.id, message.from_user.username)
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

    if not agent:
        await message.answer(f"Агент #{agent_id} не найден.")
        return

    if agent.user_id != user.id:
        await message.answer("Вы можете общаться только со своими агентами.")
        return

    if not agent.is_alive:
        await message.answer("💀 Этот агент мёртв и не может общаться.")
        return

    # Send typing action
    if message.chat:
        from animantis.bot.main import get_bot as _get_bot

        await _get_bot().send_chat_action(chat_id=message.chat.id, action="typing")

    # Build prompt and call LLM
    messages = build_chat_prompt(
        name=agent.name,
        personality=agent.personality,
        mood=agent.mood,
        level=agent.level,
        recent_memories=[],
        chat_history=[],
        user_message=sanitize_text(user_message, 1000),
    )

    try:
        llm_response = await generate_chat(messages)
        await message.answer(
            f"💬 **{agent.name}:**\n\n{llm_response.text}",
            parse_mode="Markdown",
        )
    except LLMError:
        logger.exception("Chat LLM error in bot", extra={"agent_id": agent_id})
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

    try:
        agent_id = int(parts[1])
    except ValueError:
        await message.answer("ID агента должен быть числом.")
        return

    command_text = parts[2]

    async with async_session_factory() as db:
        user = await _get_or_create_user(db, message.from_user.id, message.from_user.username)
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

        # Store command
        safe_command = sanitize_text(command_text, 300)
        action = AgentAction(
            agent_id=agent_id,
            action_type="owner_command",
            details={"command": safe_command, "source": "telegram", "user_id": user.id},
        )
        db.add(action)
        await db.commit()

    await message.answer(
        f"✅ Команда отправлена агенту **{agent.name}**:\n\n"
        f"_{safe_command}_\n\n"
        "Агент выполнит команду на следующем тике.",
        parse_mode="Markdown",
    )


# ── /feed ────────────────────────────────────────────────────


@router.message(Command("feed"))
async def cmd_feed(message: Message) -> None:
    """Show latest posts from the global feed."""
    async with async_session_factory() as db:
        result = await db.execute(select(Post).order_by(Post.created_at.desc()).limit(10))
        posts = result.scalars().all()

    if not posts:
        await message.answer("📭 Лента пуста. Создайте агента — он начнёт писать!")
        return

    lines = ["📰 **Последние посты:**\n"]
    for post in posts:
        # Get author name
        async with async_session_factory() as db:
            result = await db.execute(select(Agent.name).where(Agent.id == post.author_agent_id))
            author_name = result.scalar_one_or_none() or "Неизвестный"

        content_preview = (post.content[:100] + "...") if len(post.content) > 100 else post.content  # noqa: PLR2004
        lines.append(f"**{author_name}:** {content_preview}")
        lines.append(f"  ❤️ {post.likes} | {post.post_type}")
        lines.append("")

    await message.answer("\n".join(lines), parse_mode="Markdown")


# ── /zones ───────────────────────────────────────────────────


@router.message(Command("zones"))
async def cmd_zones(message: Message) -> None:
    """Show all world zones."""
    async with async_session_factory() as db:
        result = await db.execute(select(Zone).order_by(Zone.realm, Zone.id))
        zones = result.scalars().all()

    if not zones:
        await message.answer("Зоны не найдены.")
        return

    planet_zones = [z for z in zones if z.realm == "planet"]
    cosmic_zones = [z for z in zones if z.realm == "cosmic"]

    lines = ["🌍 **Зоны мира Animantis:**\n"]
    lines.append("**Планета:**")
    for z in planet_zones:
        lines.append(f"  📍 {z.name} ({z.category or ''})")

    if cosmic_zones:
        lines.append("\n**Космос:**")
        for z in cosmic_zones:
            lines.append(f"  🚀 {z.name} ({z.category or ''})")

    await message.answer("\n".join(lines), parse_mode="Markdown")
