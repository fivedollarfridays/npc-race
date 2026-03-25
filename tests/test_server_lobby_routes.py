"""Tests for lobby API routes (POST /api/lobby/join, GET /api/lobby/status)."""

import pytest

pytest.importorskip("fastapi")

import sqlite3

from fastapi.testclient import TestClient

from server.auth import get_db
from server.db import _create_tables, create_api_key, create_player, store_car


@pytest.fixture()
def _memory_db():
    """Provide an in-memory DB for lobby route tests."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def _fresh_lobby():
    """Reset global lobby before and after each test."""
    from server.routes.lobby import reset_lobby

    reset_lobby()
    yield
    reset_lobby()


@pytest.fixture()
def client(_memory_db: sqlite3.Connection):
    """TestClient wired to the real app with in-memory DB."""
    from server.app import app

    def _override_db():
        yield _memory_db

    app.dependency_overrides[get_db] = _override_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def authed_client(
    _memory_db: sqlite3.Connection, client: TestClient
) -> tuple[TestClient, dict]:
    """TestClient with a pre-created player and API key."""
    player = create_player(_memory_db, "TestDriver")
    key = create_api_key(_memory_db, player["id"])
    return client, {"X-API-Key": key, "id": player["id"]}


# --- GET /api/lobby/status ---


def test_lobby_status_empty(client: TestClient):
    """GET /api/lobby/status on a fresh lobby returns player_count=0."""
    resp = client.get("/api/lobby/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["player_count"] == 0
    assert data["triggered"] is False
    assert data["player_names"] == []


# --- POST /api/lobby/join ---


def test_join_lobby(
    authed_client, _memory_db: sqlite3.Connection
):
    """POST /api/lobby/join with a valid car returns 200 and joined status."""
    tc, auth = authed_client
    car_id = store_car(
        _memory_db, auth["id"], "JoinCar", "#ff0000", "def strategy(s): return {}"
    )

    resp = tc.post(
        "/api/lobby/join",
        json={"car_id": car_id},
        headers={"X-API-Key": auth["X-API-Key"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "joined"
    assert data["player_count"] == 1


def test_join_without_car(authed_client):
    """POST /api/lobby/join with invalid car_id returns 404."""
    tc, auth = authed_client
    resp = tc.post(
        "/api/lobby/join",
        json={"car_id": 9999},
        headers={"X-API-Key": auth["X-API-Key"]},
    )
    assert resp.status_code == 404
    assert "Car not found" in resp.json()["detail"]


def test_join_wrong_player(
    _memory_db: sqlite3.Connection, client: TestClient
):
    """POST /api/lobby/join with another player's car returns 403."""
    # Player A owns the car
    player_a = create_player(_memory_db, "PlayerA")
    car_id = store_car(
        _memory_db, player_a["id"], "ACar", "#00ff00", "def strategy(s): return {}"
    )

    # Player B tries to join with it
    player_b = create_player(_memory_db, "PlayerB")
    key_b = create_api_key(_memory_db, player_b["id"])

    resp = client.post(
        "/api/lobby/join",
        json={"car_id": car_id},
        headers={"X-API-Key": key_b},
    )
    assert resp.status_code == 403
    assert "Not your car" in resp.json()["detail"]


def test_lobby_status_after_join(
    authed_client, _memory_db: sqlite3.Connection
):
    """After joining, GET /api/lobby/status shows player_count=1 and name."""
    tc, auth = authed_client
    car_id = store_car(
        _memory_db, auth["id"], "StatusCar", "#0000ff", "def strategy(s): return {}"
    )

    tc.post(
        "/api/lobby/join",
        json={"car_id": car_id},
        headers={"X-API-Key": auth["X-API-Key"]},
    )

    resp = tc.get("/api/lobby/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["player_count"] == 1
    assert "StatusCar" in data["player_names"]
