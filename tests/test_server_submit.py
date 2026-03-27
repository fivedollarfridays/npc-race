"""Tests for POST /api/submit-car endpoint."""

import pytest
pytest.importorskip("fastapi")

import sqlite3

import pytest
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


# --- Validation tests ---


def test_submit_empty_source(client: TestClient, auth_headers: dict):
    """Empty source string returns 400."""
    resp = client.post(
        "/api/submit-car", json={"source": "  "}, headers=auth_headers
    )
    assert resp.status_code == 400
    assert "Empty source" in resp.json()["detail"]


def test_submit_missing_car_name(client: TestClient, auth_headers: dict):
    """Source without CAR_NAME returns 400."""
    source = 'CAR_COLOR = "#ff0000"\nPOWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20\ndef strategy(state): return {}'
    resp = client.post(
        "/api/submit-car", json={"source": source}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_submit_banned_import(client: TestClient, auth_headers: dict):
    """Source with disallowed import returns 400 with errors."""
    source = 'import os\nCAR_NAME = "Bad"\nCAR_COLOR = "#ff0000"\nPOWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20\ndef strategy(state): return {}'
    resp = client.post(
        "/api/submit-car", json={"source": source}, headers=auth_headers
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert "errors" in detail
    assert any("import" in v.lower() for v in detail["errors"])


# --- Happy path tests ---


def test_submit_valid_car(client: TestClient, auth_headers: dict):
    """POST with valid source returns 200, car_id, and name."""
    resp = client.post(
        "/api/submit-car", json={"source": VALID_CAR}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["car_id"] >= 1
    assert data["name"] == "TestCar"
    assert data["color"] == "#ff0000"
    assert data["league"] == "F3"


def test_submit_without_key_returns_401(client: TestClient):
    """POST /api/submit-car without API key returns 401."""
    resp = client.post("/api/submit-car", json={"source": VALID_CAR})
    assert resp.status_code == 401


def test_submit_existing_player(
    client: TestClient, _memory_db: sqlite3.Connection
):
    """Existing player (valid X-API-Key) gets no api_key in response."""
    player = create_player(_memory_db)
    key = create_api_key(_memory_db, player["id"])

    resp = client.post(
        "/api/submit-car",
        json={"source": VALID_CAR},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "api_key" not in data
    assert data["car_id"] >= 1
