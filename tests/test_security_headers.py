"""Tests for security headers middleware."""

import pytest


@pytest.mark.api
class TestSecurityHeaders:
    """Test SecurityHeadersMiddleware adds required headers."""

    def test_x_content_type_options(self, client):
        """Response includes X-Content-Type-Options: nosniff."""
        response = client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        """Response includes X-Frame-Options: DENY."""
        response = client.get("/health")
        assert response.headers.get("x-frame-options") == "DENY"

    def test_x_xss_protection(self, client):
        """Response includes X-XSS-Protection."""
        response = client.get("/health")
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    def test_referrer_policy(self, client):
        """Response includes Referrer-Policy."""
        response = client.get("/health")
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_hsts_in_production(self, monkeypatch):
        """HSTS header is added only in production."""
        monkeypatch.setenv("APP_ENV", "production")
        from importlib import reload

        from animantis.config import settings as settings_mod

        reload(settings_mod)

        from animantis.api import main as main_mod

        reload(main_mod)

        from fastapi.testclient import TestClient

        app = main_mod.create_app()
        prod_client = TestClient(app)
        response = prod_client.get("/health")
        assert "strict-transport-security" in response.headers
