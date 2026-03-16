"""Inline and reply keyboards for Telegram bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def agents_list_keyboard(
    agents: list[dict[str, int | str]],
) -> InlineKeyboardMarkup:
    """Build inline keyboard with user's agents.

    Args:
        agents: List of dicts with 'id' and 'name' keys.

    Returns:
        InlineKeyboardMarkup with agent buttons.
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🤖 {a['name']} (Lv.{a.get('level', 1)})",
                callback_data=f"agent_status:{a['id']}",
            )
        ]
        for a in agents
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def agent_actions_keyboard(agent_id: int) -> InlineKeyboardMarkup:
    """Build action buttons for a specific agent.

    Args:
        agent_id: Agent database ID.

    Returns:
        InlineKeyboardMarkup with action options.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Чат",
                    callback_data=f"agent_chat:{agent_id}",
                ),
                InlineKeyboardButton(
                    text="📋 Статус",
                    callback_data=f"agent_status:{agent_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Команда",
                    callback_data=f"agent_command:{agent_id}",
                ),
                InlineKeyboardButton(
                    text="📜 Посты",
                    callback_data=f"agent_posts:{agent_id}",
                ),
            ],
        ]
    )


def avatar_type_keyboard() -> InlineKeyboardMarkup:
    """Build avatar type selection keyboard."""
    avatars = [
        ("🐱 Кот", "cat"),
        ("🤖 Робот", "robot"),
        ("👻 Призрак", "ghost"),
        ("🧑 Человек", "human"),
    ]
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"avatar:{value}")]
        for label, value in avatars
    ]
    buttons.append([InlineKeyboardButton(text="⏭ Пропустить", callback_data="avatar:skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Build confirmation keyboard for agent creation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Создать!", callback_data="confirm:yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="confirm:no"),
            ]
        ]
    )
