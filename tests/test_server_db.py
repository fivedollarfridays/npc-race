"""Tests for server.db — SQLite database layer."""
import sqlite3

import pytest

from server.db import (
    create_api_key,
    create_player,
    get_car,
    get_player,
    get_player_by_api_key,
    get_player_cars,
    init_db,
    store_car,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    """In-memory database for each test."""
    return init_db(":memory:")


def test_init_db_creates_tables(conn: sqlite3.Connection) -> None:
    """init_db should create players, api_keys, and cars tables."""
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    names = [row["name"] for row in tables]
    assert "players" in names
    assert "api_keys" in names
    assert "cars" in names


def test_create_player(conn: sqlite3.Connection) -> None:
    """create_player returns a dict with id, name, created_at."""
    player = create_player(conn, name="Alice")
    assert player["name"] == "Alice"
    assert "id" in player
    assert "created_at" in player
    # Verify persisted
    row = conn.execute("SELECT * FROM players WHERE id = ?", (player["id"],)).fetchone()
    assert row is not None
    assert row["name"] == "Alice"


def test_get_player_not_found(conn: sqlite3.Connection) -> None:
    """get_player returns None for a nonexistent player."""
    assert get_player(conn, "nonexistent-id") is None


def test_create_and_get_api_key(conn: sqlite3.Connection) -> None:
    """create_api_key returns a key prefixed with 'cc_'."""
    player = create_player(conn, name="Bob")
    key = create_api_key(conn, player["id"])
    assert key.startswith("cc_")
    assert len(key) > 10


def test_get_player_by_api_key(conn: sqlite3.Connection) -> None:
    """get_player_by_api_key resolves a key to its player."""
    player = create_player(conn, name="Carol")
    key = create_api_key(conn, player["id"])
    result = get_player_by_api_key(conn, key)
    assert result is not None
    assert result["id"] == player["id"]
    assert result["name"] == "Carol"


def test_get_player_by_invalid_key(conn: sqlite3.Connection) -> None:
    """get_player_by_api_key returns None for an unknown key."""
    assert get_player_by_api_key(conn, "cc_bogus") is None


def test_store_and_get_car(conn: sqlite3.Connection) -> None:
    """store_car persists a car; get_car retrieves it."""
    player = create_player(conn, name="Dave")
    car_id = store_car(conn, player["id"], "Speedster", "#ff0000", "print('go')")
    assert isinstance(car_id, int)
    car = get_car(conn, car_id)
    assert car is not None
    assert car["name"] == "Speedster"
    assert car["color"] == "#ff0000"
    assert car["source"] == "print('go')"
    assert car["league"] == "F3"
    assert car["player_id"] == player["id"]


def test_get_player_cars_ordered(conn: sqlite3.Connection) -> None:
    """get_player_cars returns cars newest-first."""
    player = create_player(conn, name="Eve")
    id1 = store_car(conn, player["id"], "Car-A", "#aaa", "src_a")
    id2 = store_car(conn, player["id"], "Car-B", "#bbb", "src_b")
    cars = get_player_cars(conn, player["id"])
    assert len(cars) == 2
    # newest first (higher id / later created_at)
    assert cars[0]["id"] == id2
    assert cars[1]["id"] == id1


def test_get_car_not_found(conn: sqlite3.Connection) -> None:
    """get_car returns None for a nonexistent car."""
    assert get_car(conn, 99999) is None
