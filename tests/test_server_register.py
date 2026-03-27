"""Tests for POST /api/register endpoint and auth rejection (T43.5)."""

import pytest

pytest.importorskip("fastapi")

import sqlite3

from fastapi.testclient import TestClient

from server.app import app
from server.auth import get_db
from server.db import _create_tables


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


# --- Cycle 1: Register endpoint ---


def test_register_returns_api_key(client: TestClient):
    """POST /api/register returns 200 with api_key and player_id."""
    resp = client.post("/api/register")
    assert resp.status_code == 200
    data = resp.json()
    assert "api_key" in data
    assert data["api_key"].startswith("cc_")
    assert "player_id" in data


def test_register_creates_valid_player(
    client: TestClient, _memory_db: sqlite3.Connection
):
    """Registered player_id exists in the database."""
    resp = client.post("/api/register")
    player_id = resp.json()["player_id"]

    from server.db import get_player

    player = get_player(_memory_db, player_id)
    assert player is not None
    assert player["id"] == player_id


# --- Cycle 2: Unauthenticated requests return 401 ---


def test_unauthenticated_submit_returns_401(client: TestClient):
    """POST /api/submit-car without API key returns 401."""
    resp = client.post("/api/submit-car", json={"source": VALID_CAR})
    assert resp.status_code == 401
    assert "register" in resp.json()["detail"].lower()


def test_unauthenticated_cars_returns_401(client: TestClient):
    """GET /api/cars without API key returns 401."""
    resp = client.get("/api/cars")
    assert resp.status_code == 401


# --- Cycle 3: Full flow ---


def test_register_then_submit_works(client: TestClient):
    """Register, get key, submit car with key -> 200."""
    # Register
    reg = client.post("/api/register")
    assert reg.status_code == 200
    key = reg.json()["api_key"]

    # Submit car with the key
    resp = client.post(
        "/api/submit-car",
        json={"source": VALID_CAR},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["car_id"] >= 1
    assert data["name"] == "TestCar"
