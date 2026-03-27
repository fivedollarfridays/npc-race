"""Tests for UUID car IDs (T44.5)."""

import re

import pytest

pytest.importorskip("fastapi")

import sqlite3

from fastapi.testclient import TestClient

from server.app import app
from server.auth import get_db
from server.db import _create_tables, create_api_key, create_player, store_car

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)

VALID_CAR = '''
CAR_NAME = "UuidCar"
CAR_COLOR = "#ff0000"
POWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20

def strategy(state):
    return {}
'''


@pytest.fixture()
def _memory_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    yield conn
    conn.close()


@pytest.fixture()
def client(_memory_db: sqlite3.Connection):
    def _override_db():
        yield _memory_db

    app.dependency_overrides[get_db] = _override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(_memory_db: sqlite3.Connection) -> dict:
    player = create_player(_memory_db)
    key = create_api_key(_memory_db, player["id"])
    return {"X-API-Key": key}


# --- Cycle 1: car_id is UUID ---


def test_car_id_is_uuid(client: TestClient, auth_headers: dict):
    """Submitted car_id is a string matching UUID format."""
    resp = client.post(
        "/api/submit-car", json={"source": VALID_CAR}, headers=auth_headers
    )
    assert resp.status_code == 200
    car_id = resp.json()["car_id"]
    assert isinstance(car_id, str), f"car_id should be str, got {type(car_id)}"
    assert UUID_RE.match(car_id), f"car_id {car_id!r} is not a valid UUID"


def test_car_lookup_by_uuid(
    client: TestClient, auth_headers: dict, _memory_db: sqlite3.Connection
):
    """GET /api/cars/{uuid} works with UUID car IDs."""
    player = _memory_db.execute("SELECT id FROM players").fetchone()
    car_id = store_car(
        _memory_db, player["id"], "LookupCar", "#00ff00", "def strategy(s): return {}"
    )
    assert isinstance(car_id, str)
    assert UUID_RE.match(car_id)

    resp = client.get(f"/api/cars/{car_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "LookupCar"


def test_sequential_ids_not_used(
    _memory_db: sqlite3.Connection,
):
    """Two cars have different non-sequential UUIDs."""
    player = create_player(_memory_db, "SeqTest")
    id1 = store_car(
        _memory_db, player["id"], "Car1", "#ff0000", "def strategy(s): return {}"
    )
    id2 = store_car(
        _memory_db, player["id"], "Car2", "#0000ff", "def strategy(s): return {}"
    )
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert id1 != id2
    # Not sequential integers
    assert UUID_RE.match(id1)
    assert UUID_RE.match(id2)
