"""Tests for Pydantic response models on server routes."""

import pytest

pytest.importorskip("fastapi")

import sqlite3

from fastapi.testclient import TestClient

from server.auth import get_db
from server.db import _create_tables, create_api_key, create_player


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


# --- Health response model tests ---


def test_health_model_exists():
    """HealthResponse Pydantic model can be imported."""
    from server.routes.health import HealthResponse

    m = HealthResponse(status="ok", version="0.1.0")
    assert m.status == "ok"
    assert m.version == "0.1.0"


def test_health_endpoint_uses_model(client: TestClient):
    """GET /api/health returns exactly the model fields, no extras."""
    resp = client.get("/api/health")
    data = resp.json()
    assert set(data.keys()) == {"status", "version"}


# --- Tracks response model tests ---


def test_track_response_model_exists():
    """TrackResponse Pydantic model can be imported."""
    from server.routes.tracks import TrackResponse

    m = TrackResponse(
        name="monza",
        country="Italy",
        character="high-speed",
        laps_default=5,
        real_length_m=5793.0,
    )
    assert m.name == "monza"


def test_tracks_list_response_model_exists():
    """TracksListResponse Pydantic model can be imported."""
    from server.routes.tracks import TrackResponse, TracksListResponse

    t = TrackResponse(
        name="monza",
        country="Italy",
        character="high-speed",
        laps_default=5,
        real_length_m=5793.0,
    )
    m = TracksListResponse(tracks=[t], count=1)
    assert m.count == 1
    assert len(m.tracks) == 1


def test_tracks_endpoint_uses_model(client: TestClient):
    """GET /api/tracks returns response matching TracksListResponse schema."""
    resp = client.get("/api/tracks")
    data = resp.json()
    assert set(data.keys()) == {"tracks", "count"}
    for track in data["tracks"]:
        assert "name" in track
        assert "country" in track
        assert "character" in track
        assert "laps_default" in track


# --- Cars response model tests ---


def test_car_list_response_model_exists():
    """CarListResponse Pydantic model can be imported."""
    from server.routes.cars import CarListResponse

    m = CarListResponse(cars=[])
    assert m.cars == []


def test_car_detail_response_model_exists():
    """CarDetailResponse Pydantic model can be imported."""
    from server.routes.cars import CarDetailResponse

    m = CarDetailResponse(
        id="abc-123",
        name="MyCar",
        color="#ff0000",
        league="F3",
        source="def setup(car): pass",
        player_id="player-1",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    assert m.name == "MyCar"
    assert m.id == "abc-123"


def test_cars_list_endpoint_uses_model(authed_client):
    """GET /api/cars returns response matching CarListResponse schema."""
    client, auth = authed_client
    resp = client.get("/api/cars", headers={"X-API-Key": auth["X-API-Key"]})
    data = resp.json()
    assert "cars" in data
