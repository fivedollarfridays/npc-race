"""Tests for server app skeleton, config, CORS, and static mount."""

import pytest
pytest.importorskip("fastapi")


def test_app_exists():
    """Import server.app and verify app object exists."""
    from server.app import app

    assert app is not None
    assert app.title == "Code Circuit"
    assert app.version == "0.1.0"


def test_settings_defaults():
    """Config Settings has correct default values."""
    from server.config import Settings

    s = Settings()
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.db_path == "data/npcrace.db"
    assert "http://localhost:8000" in s.cors_origins
    assert "http://localhost:3000" in s.cors_origins
    assert "http://127.0.0.1:8000" in s.cors_origins
    assert s.static_dir == "server/static"
    assert s.viewer_dir == "viewer"


def test_cors_configured():
    """CORS middleware is present on the app."""
    from server.app import app

    cors_found = any("CORS" in str(m.cls) for m in app.user_middleware)
    assert cors_found, f"CORS middleware not found in {app.user_middleware}"


def test_static_mount():
    """The /static route is mounted."""
    from server.app import app

    route_paths = [r.path for r in app.routes]
    assert "/static" in route_paths, f"/static not in {route_paths}"


def test_viewer_mount():
    """The /viewer route is mounted."""
    from server.app import app

    route_paths = [r.path for r in app.routes]
    assert "/viewer" in route_paths, f"/viewer not in {route_paths}"


def test_static_serves_index():
    """GET /static/index.html returns 200."""
    from fastapi.testclient import TestClient

    from server.app import app

    client = TestClient(app)
    resp = client.get("/static/index.html")
    assert resp.status_code == 200
    assert "Code Circuit" in resp.text
