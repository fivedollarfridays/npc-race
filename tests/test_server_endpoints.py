"""Tests for cars and tracks API endpoints."""

import pytest
pytest.importorskip("fastapi")

import sqlite3

import pytest
from fastapi.testclient import TestClient

from server.auth import get_db
from server.db import _create_tables, create_api_key, create_player, store_car


@pytest.fixture()
def _memory_db():
    """Provide an in-memory DB for endpoint tests."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    yield conn
    conn.close()


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


# --- Tracks tests ---


def test_tracks_returns_20(client: TestClient):
    """GET /api/tracks returns 200 with count == 20."""
    resp = client.get("/api/tracks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 20
    assert len(data["tracks"]) == 20


def test_tracks_have_metadata(client: TestClient):
    """Each track has name, country, character, laps_default."""
    resp = client.get("/api/tracks")
    for track in resp.json()["tracks"]:
        assert "name" in track
        assert "country" in track
        assert "character" in track
        assert "laps_default" in track


# --- Cars tests ---


def test_cars_empty_for_new_player(authed_client):
    """GET /api/cars with a fresh player returns empty list."""
    client, auth = authed_client
    resp = client.get("/api/cars", headers={"X-API-Key": auth["X-API-Key"]})
    assert resp.status_code == 200
    assert resp.json()["cars"] == []


def test_cars_after_submit(
    authed_client, _memory_db: sqlite3.Connection
):
    """After storing a car, GET /api/cars returns 1 car."""
    client, auth = authed_client
    store_car(_memory_db, auth["id"], "MyCar", "#ff0000", "def setup(car): pass")

    resp = client.get("/api/cars", headers={"X-API-Key": auth["X-API-Key"]})
    assert resp.status_code == 200
    cars = resp.json()["cars"]
    assert len(cars) == 1
    assert cars[0]["name"] == "MyCar"
    assert cars[0]["color"] == "#ff0000"


def test_car_detail(
    authed_client, _memory_db: sqlite3.Connection
):
    """GET /api/cars/{id} returns full car data."""
    client, auth = authed_client
    car_id = store_car(
        _memory_db, auth["id"], "DetailCar", "#00ff00", "def setup(car): pass"
    )

    resp = client.get(
        f"/api/cars/{car_id}", headers={"X-API-Key": auth["X-API-Key"]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "DetailCar"
    assert data["source"] == "def setup(car): pass"


def test_car_not_found(authed_client):
    """GET /api/cars/999 with valid auth returns 404."""
    client, auth = authed_client
    resp = client.get("/api/cars/999", headers={"X-API-Key": auth["X-API-Key"]})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Car not found"
