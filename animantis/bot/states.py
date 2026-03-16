"""FSM states for Telegram bot."""

from aiogram.fsm.state import State, StatesGroup


class AgentCreation(StatesGroup):
    """States for multi-step agent creation."""

    name = State()  # Waiting for agent name
    personality = State()  # Waiting for personality description
    backstory = State()  # Waiting for backstory (optional)
    avatar_type = State()  # Waiting for avatar type
    confirmation = State()  # Confirm creation
