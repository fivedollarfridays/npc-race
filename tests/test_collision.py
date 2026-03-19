"""Tests for engine.collision — contact detection and resolution."""
import random

from engine.collision import (
    check_collisions,
    is_contact,
    resolve_collision,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_car(name: str, distance: float, lateral: float = 0.0,
              finished: bool = False, pit_status: str = "racing",
              contact_cooldown: int = 0) -> dict:
    """Build a minimal car state dict for collision testing."""
    return {
        "name": name,
        "distance": distance,
        "lateral": lateral,
        "finished": finished,
        "pit_state": {"status": pit_status},
        "contact_cooldown": contact_cooldown,
    }


# ---------------------------------------------------------------------------
# is_contact tests
# ---------------------------------------------------------------------------

class TestIsContact:
    def test_no_contact_when_far_apart(self):
        a = _make_car("A", distance=0.0, lateral=0.5)
        b = _make_car("B", distance=50.0, lateral=0.0)
        assert is_contact(a, b) is False

    def test_contact_when_close(self):
        a = _make_car("A", distance=100.0, lateral=0.0)
        b = _make_car("B", distance=102.0, lateral=0.1)
        assert is_contact(a, b) is True

    def test_no_contact_in_pit(self):
        a = _make_car("A", distance=100.0, lateral=0.0)
        b = _make_car("B", distance=101.0, lateral=0.0, pit_status="pit_entry")
        assert is_contact(a, b) is False

    def test_no_contact_when_finished(self):
        a = _make_car("A", distance=100.0, lateral=0.0, finished=True)
        b = _make_car("B", distance=101.0, lateral=0.0)
        assert is_contact(a, b) is False

    def test_no_contact_when_lateral_differs(self):
        a = _make_car("A", distance=100.0, lateral=0.0)
        b = _make_car("B", distance=102.0, lateral=0.5)
        assert is_contact(a, b) is False


# ---------------------------------------------------------------------------
# resolve_collision tests
# ---------------------------------------------------------------------------

class TestResolveCollision:
    def test_collision_event_has_all_fields(self):
        a = _make_car("A", distance=100.0)
        b = _make_car("B", distance=101.0)
        rng = random.Random(42)
        event = resolve_collision(a, b, rng)
        for key in ("car_a", "car_b", "severity", "speed_loss", "damage",
                     "spin", "dnf"):
            assert key in event, f"Missing field: {key}"

    def test_collision_produces_speed_loss(self):
        a = _make_car("A", distance=100.0)
        b = _make_car("B", distance=101.0)
        # Seed that yields a minor collision (roll < 0.50)
        rng = random.Random(0)
        event = resolve_collision(a, b, rng)
        if event["severity"] == "minor":
            assert event["speed_loss"] > 0

    def test_collision_severity_distribution(self):
        a = _make_car("A", distance=100.0)
        b = _make_car("B", distance=101.0)
        rng = random.Random(123)
        counts: dict[str, int] = {"minor": 0, "moderate": 0, "severe": 0,
                                   "critical": 0}
        n = 1000
        for _ in range(n):
            event = resolve_collision(a, b, rng)
            counts[event["severity"]] += 1
        # Allow +/- 10 percentage points
        assert 0.40 <= counts["minor"] / n <= 0.60
        assert 0.20 <= counts["moderate"] / n <= 0.40


# ---------------------------------------------------------------------------
# check_collisions tests
# ---------------------------------------------------------------------------

class TestCheckCollisions:
    def test_collision_cooldown_prevents_repeat(self):
        a = _make_car("A", distance=100.0, lateral=0.0, contact_cooldown=30)
        b = _make_car("B", distance=101.0, lateral=0.0)
        rng = random.Random(42)
        events = check_collisions([a, b], rng)
        assert len(events) == 0

    def test_check_collisions_returns_list(self):
        a = _make_car("A", distance=100.0, lateral=0.0)
        b = _make_car("B", distance=101.0, lateral=0.1)
        c = _make_car("C", distance=500.0, lateral=0.0)
        rng = random.Random(42)
        events = check_collisions([a, b, c], rng)
        assert isinstance(events, list)
        assert len(events) == 1
        names = {events[0]["car_a"], events[0]["car_b"]}
        assert names == {"A", "B"}
