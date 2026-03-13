"""Tests for API health and ping endpoints."""

import pytest


@pytest.mark.api
class TestHealthEndpoints:
    """Test /health and /api/v1/ping."""

    def test_health_returns_200(self, client):
        """GET /health → 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "animantis-api"

    def test_ping_returns_pong(self, client):
        """GET /api/v1/ping → 200 with pong message."""
        response = client.get("/api/v1/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "pong"
        assert data["version"] == "0.1.0"

    def test_nonexistent_route_returns_404(self, client):
        """GET /nonexistent → 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
