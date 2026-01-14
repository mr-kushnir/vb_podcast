"""
Unit tests for Main FastAPI Application
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


class TestMainApp:
    """Test FastAPI application endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_check_returns_200(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["service"] == "ai-morning-podcast"

    def test_root_returns_api_message(self, client):
        """Test root endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AI Morning Podcast Portal API" in data["message"]

    def test_app_has_cors_middleware(self):
        """Test that CORS middleware is configured"""
        # Check middleware is registered
        assert len(app.user_middleware) > 0

    def test_app_includes_portal_routes(self):
        """Test that portal routes are included"""
        routes = [route.path for route in app.routes]
        assert any("/api" in path for path in routes)

    def test_app_includes_automation_routes(self):
        """Test that automation routes are included"""
        routes = [route.path for route in app.routes]
        assert any("/api/automation" in path for path in routes)

    def test_app_metadata(self):
        """Test app metadata"""
        assert app.title == "AI Morning Podcast Portal"
        assert "Daily AI news podcast" in app.description
        assert app.version == "1.0.0"

    def test_portal_episodes_endpoint(self, client):
        """Test portal episodes endpoint"""
        response = client.get("/api/episodes")

        assert response.status_code == 200
        data = response.json()
        assert "episodes" in data

    def test_automation_generate_endpoint(self, client):
        """Test automation generate endpoint"""
        response = client.post("/api/automation/generate")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
