"""Tests for application settings and configuration."""

import pytest


@pytest.mark.unit
class TestSettings:
    """Test Settings class from config/settings.py."""

    def test_default_app_env(self, monkeypatch):
        """Default APP_ENV is 'development' (overridden to 'test' in conftest)."""
        monkeypatch.setenv("APP_ENV", "development")
        from importlib import reload

        from animantis.config import settings as settings_mod

        reload(settings_mod)
        s = settings_mod.Settings()
        assert s.APP_ENV == "development"

    def test_env_override(self, monkeypatch):
        """Settings can be overridden via environment variables."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("MAX_AGENTS_PER_USER", "10")
        from importlib import reload

        from animantis.config import settings as settings_mod

        reload(settings_mod)
        s = settings_mod.Settings()
        assert s.APP_ENV == "production"
        assert s.DEBUG is False
        assert s.MAX_AGENTS_PER_USER == 10

    def test_yandex_gpt_lite_uri(self, monkeypatch):
        """yandex_gpt_lite_uri is computed from YANDEX_FOLDER_ID."""
        monkeypatch.setenv("YANDEX_FOLDER_ID", "b1g12345")
        from importlib import reload

        from animantis.config import settings as settings_mod

        reload(settings_mod)
        s = settings_mod.Settings()
        assert s.yandex_gpt_lite_uri == "gpt://b1g12345/yandexgpt-lite/latest"

    def test_yandex_gpt_pro_uri(self, monkeypatch):
        """yandex_gpt_pro_uri is computed from YANDEX_FOLDER_ID."""
        monkeypatch.setenv("YANDEX_FOLDER_ID", "b1g12345")
        from importlib import reload

        from animantis.config import settings as settings_mod

        reload(settings_mod)
        s = settings_mod.Settings()
        assert s.yandex_gpt_pro_uri == "gpt://b1g12345/yandexgpt/latest"

    def test_rate_limit_defaults(self):
        """Rate limit defaults match project rules."""
        from animantis.config.settings import Settings

        s = Settings()
        assert s.RATE_LIMIT_API == 60
        assert s.RATE_LIMIT_AGENT_CREATE == 5
        assert s.RATE_LIMIT_CHAT == 20

    def test_agent_limit_defaults(self):
        """Agent limits have correct defaults."""
        from animantis.config.settings import Settings

        s = Settings()
        assert s.MAX_AGENTS_PER_USER == 5
        assert s.AGENT_TICK_TIMEOUT == 30
