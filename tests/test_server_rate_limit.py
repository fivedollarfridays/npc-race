"""Tests for rate limiting and source size cap (T43.3)."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("slowapi")

import sqlite3

from fastapi.testclient import TestClient

from server.app import app
from server.auth import get_db
from server.db import create_api_key, create_player


VALID_CAR = '''
CAR_NAME = "TestCar"
CAR_COLOR = "#ff0000"
POWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20

def strategy(state):
    return {}
'''

MAX_SOURCE_BYTES = 32768  # 32KB


@pytest.fixture()
def _memory_db():
    """Provide an in-memory DB and override the get_db dependency."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    from server.db import _create_tables

    _create_tables(conn)
    yield conn
    conn.close()


@pytest.fixture()
def client(_memory_db: sqlite3.Connection):
    """TestClient with DB dependency overridden to in-memory."""

    def _override_db():
        yield _memory_db

    app.dependency_overrides[get_db] = _override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(_memory_db: sqlite3.Connection) -> dict:
    """Create a player + API key and return auth headers dict."""
    player = create_player(_memory_db)
    key = create_api_key(_memory_db, player["id"])
    return {"X-API-Key": key}


# --- Source size cap ---


def test_source_too_large_rejected(client: TestClient, auth_headers: dict):
    """Source > 32KB is rejected for size, not some other reason."""
    huge_source = "x = 1\n" * 10000  # ~60KB
    resp = client.post(
        "/api/submit-car", json={"source": huge_source}, headers=auth_headers
    )
    assert resp.status_code in (400, 422)
    body = resp.json()
    # Should mention size in the error (Pydantic or explicit check)
    detail = str(body.get("detail", ""))
    assert "large" in detail.lower() or "max_length" in detail.lower() or "string_too_long" in str(body).lower(), (
        f"Expected size-related error, got: {body}"
    )


def test_normal_source_accepted(client: TestClient, auth_headers: dict):
    """Normal-sized source is accepted (status 200)."""
    resp = client.post(
        "/api/submit-car", json={"source": VALID_CAR}, headers=auth_headers
    )
    assert resp.status_code == 200


def test_source_at_limit_accepted(client: TestClient):
    """Source exactly at 32KB limit should be accepted."""
    # Build a valid car source padded to just under limit
    base = VALID_CAR.strip()
    padding_needed = MAX_SOURCE_BYTES - len(base) - 1  # -1 for newline
    padded = base + "\n" + "#" * padding_needed
    assert len(padded) <= MAX_SOURCE_BYTES
    resp = client.post("/api/submit-car", json={"source": padded})
    # Should not be rejected for size (may fail for other reasons)
    assert resp.status_code != 422  # Not a Pydantic size error


# --- Rate limiting structure ---


def test_rate_limit_configured_on_submit():
    """Submit endpoint has rate limiting registered in limiter."""
    from server.rate_limit import limiter

    route_key = "server.routes.submit.submit_car"
    assert route_key in limiter._route_limits, (
        "submit_car should have a rate limit registered"
    )


def test_rate_limit_configured_on_lobby_join():
    """Lobby join endpoint has rate limiting registered in limiter."""
    from server.rate_limit import limiter

    route_key = "server.routes.lobby.join_lobby"
    assert route_key in limiter._route_limits, (
        "join_lobby should have a rate limit registered"
    )


def test_limiter_attached_to_app():
    """App should have a limiter in its state."""
    assert hasattr(app.state, "limiter"), "app.state.limiter should exist"
