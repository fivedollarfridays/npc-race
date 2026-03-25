"""Tests for server.auth — API key authentication."""

import pytest
pytest.importorskip("fastapi")

import sqlite3

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from server.auth import get_current_player, get_db
from server.db import create_api_key, create_player


@pytest.fixture()
def _memory_db():
    """Provide an in-memory DB and override the get_db dependency."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Reuse init_db's table creation via private helper
    from server.db import _create_tables

    _create_tables(conn)
    yield conn
    conn.close()


@pytest.fixture()
def client(_memory_db: sqlite3.Connection):
    """TestClient with auth dependency wired to in-memory DB."""
    app = FastAPI()

    def _override_db():
        yield _memory_db

    app.dependency_overrides[get_db] = _override_db

    @app.get("/test-auth")
    async def _test_auth(player=Depends(get_current_player)):
        return player

    return TestClient(app)


# --- Tests ---


def test_no_key_creates_player(client: TestClient):
    """Request without X-API-Key auto-creates player and returns api_key."""
    resp = client.get("/test-auth")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "api_key" in data
    assert data["api_key"].startswith("cc_")
    assert data["_new"] is True


def test_valid_key_returns_player(
    client: TestClient, _memory_db: sqlite3.Connection
):
    """Request with valid X-API-Key returns the correct player."""
    player = create_player(_memory_db)
    key = create_api_key(_memory_db, player["id"])

    resp = client.get("/test-auth", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == player["id"]
    assert "api_key" not in data  # existing players don't get key echoed


def test_invalid_key_returns_401(client: TestClient):
    """Request with an invalid X-API-Key returns 401."""
    resp = client.get("/test-auth", headers={"X-API-Key": "cc_bogus"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid API key"
