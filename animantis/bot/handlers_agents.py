"""Bot handlers — agent management (/create, /my, /status)."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from animantis.bot.keyboards import (
    agent_actions_keyboard,
    agents_list_keyboard,
    avatar_type_keyboard,
    confirm_keyboard,
)
from animantis.bot.states import AgentCreation
from animantis.bot.utils import (
    _get_or_create_user,
    _get_user_agents,
    _get_zone_name,
    _mood_emoji,
    async_session_factory,
)
from animantis.db.models import Agent

logger = logging.getLogger("animantis")

router = Router(name="handlers_agents")


# ── /create (FSM) ────────────────────────────────────────────


@router.message(Command("create"))
async def cmd_create(message: Message, state: FSMContext) -> None:
    """Start agent creation — step 1: name."""
    if not message.from_user:
        return

    async with async_session_factory() as db:
        user = await _get_or_create_user(
            db,
            message.from_user.id,
            message.from_user.username,
        )
        agents = await _get_user_agents(db, user.id)

    if len(agents) >= 5:  # noqa: PLR2004
        await message.answer(
            "⚠️ Максимум 5 агентов. Удалите одного, чтобы создать нового.",
        )
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
    """Process personality — step 3: avatar."""
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

    if callback.data.split(":")[1] != "yes":
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
            zone_id=1,
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
        user = await _get_or_create_user(
            db,
            message.from_user.id,
            message.from_user.username,
        )
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
        await message.answer(
            "Используйте: /status `<id агента>`",
            parse_mode="Markdown",
        )
        return

    agent_id = _parse_agent_id(parts[1])
    if agent_id is None:
        await message.answer("ID агента должен быть числом.")
        return

    async with async_session_factory() as db:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

    if not agent:
        await message.answer(f"Агент #{agent_id} не найден.")
        return

    zone_name = await _get_zone_name(agent.zone_id)
    alive = "💚" if agent.is_alive else "💀"

    text = (
        f"{alive} **{agent.name}**\n\n"
        f"📊 Уровень: {agent.level} (XP: {agent.xp})\n"
        f"⚡ Энергия: {agent.energy}/100\n"
        f"{_mood_emoji(agent.mood)} Настроение: {agent.mood}\n"
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

    zone_name = await _get_zone_name(agent.zone_id)
    alive = "💚" if agent.is_alive else "💀"

    text = (
        f"{alive} **{agent.name}**\n\n"
        f"📊 Lv.{agent.level} | ⚡ {agent.energy}/100 | 💰 {agent.coins}\n"
        f"😌 {agent.mood} | ⭐ {agent.reputation}\n"
        f"📍 {zone_name} | 🔄 {agent.total_ticks} тиков"
    )
    try:
        await callback.message.edit_text(  # type: ignore[union-attr]
            text,
            parse_mode="Markdown",
            reply_markup=agent_actions_keyboard(agent.id),
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


# ── Private helpers ──────────────────────────────────────────


def _parse_agent_id(raw: str) -> int | None:
    """Try to parse agent ID from string."""
    try:
        return int(raw)
    except ValueError:
        return None
