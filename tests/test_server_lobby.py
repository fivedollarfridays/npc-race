"""Tests for the race lobby system."""
import time

import pytest


def _make_car(player_id: str = "p1", name: str = "TestCar") -> dict:
    return {
        "car_id": f"car-{player_id}",
        "player_id": player_id,
        "name": name,
        "color": "#FF0000",
        "source": "class Car: pass",
    }


def test_join_adds_player():
    from server.lobby import Lobby

    lobby = Lobby()
    result = lobby.join(_make_car("p1", "Alice"))
    assert result["player_count"] == 1
    assert result["triggered"] is False


def test_status_shows_names():
    from server.lobby import Lobby

    lobby = Lobby()
    lobby.join(_make_car("p1", "Alice"))
    lobby.join(_make_car("p2", "Bob"))
    status = lobby.status()
    assert status["player_names"] == ["Alice", "Bob"]
    assert status["player_count"] == 2


def test_join_multiple():
    from server.lobby import Lobby

    lobby = Lobby()
    for i in range(3):
        lobby.join(_make_car(f"p{i}", f"Player{i}"))
    assert lobby.status()["player_count"] == 3


def test_join_full_raises():
    from server.lobby import Lobby, LobbyFullError, MAX_PLAYERS

    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_car(f"p{i}", f"Player{i}"))
    with pytest.raises(LobbyFullError):
        lobby.join(_make_car("extra", "Extra"))


def test_join_duplicate_raises():
    from server.lobby import Lobby, LobbyDuplicateError

    lobby = Lobby()
    lobby.join(_make_car("p1", "Alice"))
    with pytest.raises(LobbyDuplicateError):
        lobby.join(_make_car("p1", "Alice Again"))


def test_trigger_on_timeout():
    from server.lobby import Lobby

    lobby = Lobby()
    lobby.join(_make_car("p1", "Alice"))
    # Force the timer to have expired
    lobby._created_at = time.monotonic() - 61.0
    assert lobby.check_trigger() is True
    assert lobby.triggered is True


def test_trigger_on_full():
    from server.lobby import Lobby, MAX_PLAYERS

    lobby = Lobby()
    for i in range(MAX_PLAYERS):
        lobby.join(_make_car(f"p{i}", f"Player{i}"))
    assert lobby.check_trigger() is True
    assert lobby.triggered is True


def test_triggered_lobby_rejects_join():
    from server.lobby import Lobby, LobbyClosedError

    lobby = Lobby()
    lobby.join(_make_car("p1", "Alice"))
    lobby._created_at = time.monotonic() - 61.0
    lobby.check_trigger()
    with pytest.raises(LobbyClosedError):
        lobby.join(_make_car("p2", "Bob"))


def test_race_id_set_on_trigger():
    import uuid

    from server.lobby import Lobby

    lobby = Lobby()
    lobby.join(_make_car("p1", "Alice"))
    assert lobby.race_id is None
    lobby._created_at = time.monotonic() - 61.0
    lobby.check_trigger()
    assert lobby.race_id is not None
    # Verify it's a valid UUID
    uuid.UUID(lobby.race_id)
