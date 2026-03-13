"""Shared test fixtures for Animantis."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set minimal environment variables for tests."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-32-chars-minimum!")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("YANDEX_API_KEY", "test-key")
    monkeypatch.setenv("YANDEX_FOLDER_ID", "test-folder")


@pytest.fixture()
def app():
    """Create a fresh FastAPI app for each test."""
    # Re-import to get fresh Settings with test env
    from animantis.api.main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    """FastAPI TestClient."""
    return TestClient(app)
