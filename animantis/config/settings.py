"""Animantis configuration — Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"  # noqa: S105

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/railway"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""

    # YandexGPT
    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""

    # Frontend
    FRONTEND_URL: str = "https://animantis.ru"
    DOMAIN: str = "animantis.ru"

    # LLM endpoints (auto-computed)
    @property
    def yandex_gpt_lite_uri(self) -> str:
        return f"gpt://{self.YANDEX_FOLDER_ID}/yandexgpt-lite/latest"

    @property
    def yandex_gpt_pro_uri(self) -> str:
        return f"gpt://{self.YANDEX_FOLDER_ID}/yandexgpt/latest"

    # Rate limits
    RATE_LIMIT_API: int = 60          # req/min general
    RATE_LIMIT_AGENT_CREATE: int = 5  # per hour
    RATE_LIMIT_CHAT: int = 20         # per min

    # Agent limits
    MAX_AGENTS_PER_USER: int = 5
    AGENT_TICK_TIMEOUT: int = 30      # seconds

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
