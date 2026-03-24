"""Tests for GET /api/health endpoint."""

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_returns_status_ok():
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_version():
    response = client.get("/api/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"
