"""Tests for Telegram notification service."""

from unittest.mock import AsyncMock, patch

import pytest

from animantis.bot.notifications import (
    notify_clan_invite,
    notify_death,
    notify_level_up,
    notify_low_energy,
    notify_relationship,
    notify_world_event,
)


@pytest.fixture()
def mock_bot():
    """Create a mock aiogram Bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=True)
    return bot


@pytest.mark.asyncio()
async def test_notify_level_up(mock_bot):  # noqa: S107
    """Level up notification sends correct message."""
    result = await notify_level_up(mock_bot, 123456, "Алиса", 5)
    assert result is True
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert "Алиса" in call_args.kwargs["text"]
    assert "5" in call_args.kwargs["text"]
    assert "🎉" in call_args.kwargs["text"]


@pytest.mark.asyncio()
async def test_notify_death(mock_bot):
    """Death notification sends correct emoji and message."""
    result = await notify_death(mock_bot, 123456, "Боб")
    assert result is True
    call_args = mock_bot.send_message.call_args
    assert "☠️" in call_args.kwargs["text"]
    assert "Боб" in call_args.kwargs["text"]


@pytest.mark.asyncio()
async def test_notify_low_energy(mock_bot):
    """Low energy notification shows energy value."""
    result = await notify_low_energy(mock_bot, 123456, "Алиса", 5)
    assert result is True
    call_args = mock_bot.send_message.call_args
    assert "5" in call_args.kwargs["text"]
    assert "⚡" in call_args.kwargs["text"]


@pytest.mark.asyncio()
async def test_notify_relationship(mock_bot):
    """Relationship notification shows correct icon per type."""
    result = await notify_relationship(
        mock_bot,
        123456,
        "Алиса",
        "Боб",
        "friend",
    )
    assert result is True
    call_args = mock_bot.send_message.call_args
    assert "🤝" in call_args.kwargs["text"]


@pytest.mark.asyncio()
async def test_notify_world_event(mock_bot):
    """World event notification contains event name."""
    result = await notify_world_event(
        mock_bot,
        123456,
        "Шторм",
        "Все зоны скованы льдом",
    )
    assert result is True
    call_args = mock_bot.send_message.call_args
    assert "Шторм" in call_args.kwargs["text"]
    assert "🌍" in call_args.kwargs["text"]


@pytest.mark.asyncio()
async def test_notify_clan_invite(mock_bot):
    """Clan invite notification shows clan name."""
    result = await notify_clan_invite(mock_bot, 123456, "Алиса", "Огненные коты")
    assert result is True
    call_args = mock_bot.send_message.call_args
    assert "Огненные коты" in call_args.kwargs["text"]


@pytest.mark.asyncio()
async def test_send_notification_api_error(mock_bot):
    """Notification failure returns False (no exception)."""
    from aiogram.exceptions import TelegramAPIError

    mock_bot.send_message.side_effect = TelegramAPIError(
        method="sendMessage",
        message="Forbidden: bot was blocked by the user",
    )
    with patch("animantis.bot.notifications.logger"):
        result = await notify_level_up(mock_bot, 999, "Test", 1)
    assert result is False
