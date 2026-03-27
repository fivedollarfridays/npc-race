"""Tests for car endpoint auth + ownership checks (T43.1)."""

import pytest

pytest.importorskip("fastapi")

import sqlite3

from fastapi.testclient import TestClient

from server.app import app
from server.auth import get_db
from server.db import _create_tables, create_api_key, create_player, store_car


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


def _make_player_with_car(conn: sqlite3.Connection, name: str = "Player") -> tuple:
    """Create a player, API key, and car. Return (key, car_id)."""
    player = create_player(conn, name)
    key = create_api_key(conn, player["id"])
    car_id = store_car(conn, player["id"], "MyCar", "#ff0000", "print('hi')")
    return key, car_id


# --- Cycle 1: Auth required ---


def test_invalid_key_car_detail_returns_401(client: TestClient):
    """GET /api/cars/1 with invalid API key returns 401."""
    resp = client.get("/api/cars/1", headers={"X-API-Key": "cc_bogus"})
    assert resp.status_code == 401


# --- Cycle 2: Ownership check ---


def test_other_players_car_returns_404(
    client: TestClient, _memory_db: sqlite3.Connection
):
    """GET /api/cars/{id} for another player's car returns 404."""
    _key_a, car_id = _make_player_with_car(_memory_db, "PlayerA")
    key_b, _car_id_b = _make_player_with_car(_memory_db, "PlayerB")

    resp = client.get(f"/api/cars/{car_id}", headers={"X-API-Key": key_b})
    assert resp.status_code == 404


# --- Cycle 3: Happy path ---


def test_own_car_returns_200(client: TestClient, _memory_db: sqlite3.Connection):
    """GET /api/cars/{id} for own car returns full data including source."""
    key, car_id = _make_player_with_car(_memory_db)

    resp = client.get(f"/api/cars/{car_id}", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == car_id
    assert data["name"] == "MyCar"
    assert "source" in data


# --- Cycle 4: List excludes source ---


def test_cars_list_excludes_source(
    client: TestClient, _memory_db: sqlite3.Connection
):
    """GET /api/cars list does not include source field."""
    key, _car_id = _make_player_with_car(_memory_db)

    resp = client.get("/api/cars", headers={"X-API-Key": key})
    assert resp.status_code == 200
    cars = resp.json()["cars"]
    assert len(cars) >= 1
    for car in cars:
        assert "source" not in car
