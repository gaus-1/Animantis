"""Telegram bot initialization — aiogram 3 + webhook mode."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from animantis.bot.handlers import router as handlers_router
from animantis.config.settings import settings

logger = logging.getLogger("animantis")


def create_bot() -> Bot:
    """Create aiogram Bot instance."""
    return Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def create_dispatcher() -> Dispatcher:
    """Create aiogram Dispatcher with FSM storage and handlers."""
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(handlers_router)
    return dp


# Singleton instances (created once, reused across requests)
bot: Bot | None = None
dp: Dispatcher | None = None


def get_bot() -> Bot:
    """Get or create Bot singleton."""
    global bot  # noqa: PLW0603
    if bot is None:
        bot = create_bot()
    return bot


def get_dispatcher() -> Dispatcher:
    """Get or create Dispatcher singleton."""
    global dp  # noqa: PLW0603
    if dp is None:
        dp = create_dispatcher()
    return dp


async def setup_webhook() -> None:
    """Set Telegram webhook URL.

    Called once at application startup.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping webhook setup")
        return

    if not settings.TELEGRAM_WEBHOOK_URL:
        logger.warning("TELEGRAM_WEBHOOK_URL not set, skipping webhook setup")
        return

    b = get_bot()
    webhook_url = settings.TELEGRAM_WEBHOOK_URL
    logger.info("Setting webhook", extra={"url": webhook_url})

    await b.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
    )
    logger.info("Webhook set successfully")


async def shutdown_bot() -> None:
    """Cleanup on application shutdown."""
    global bot, dp  # noqa: PLW0603
    if bot:
        await bot.session.close()
        bot = None
    dp = None
