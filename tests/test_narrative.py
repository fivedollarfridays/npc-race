"""Tests for race event detection (T13.1)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.narrative import (
    detect_events, detect_overtakes, detect_battles,
    detect_incidents, detect_pit_stops, detect_fastest_laps,
)


def _frame(cars):
    """Build a single replay frame from car dicts."""
    return [{"name": c.get("name", f"Car{i}"), "position": c.get("position", i + 1),
             "speed": c.get("speed", 200), "gap_ahead_s": c.get("gap_ahead_s", 0),
             "pit_status": c.get("pit_status", "racing"),
             "in_spin": c.get("in_spin", False),
             "safety_car": c.get("safety_car", False),
             "finished": c.get("finished", False),
             "lap": c.get("lap", 1),
             "tire_compound": c.get("tire_compound", "medium")}
            for i, c in enumerate(cars)]


class TestDetectOvertakes:
    def test_detect_overtake(self):
        f1 = _frame([{"name": "A", "position": 1}, {"name": "B", "position": 2}])
        f2 = _frame([{"name": "A", "position": 2}, {"name": "B", "position": 1}])
        events = detect_overtakes([f1, f2])
        assert any(e.type == "OVERTAKE" for e in events)

    def test_event_has_required_fields(self):
        f1 = _frame([{"name": "A", "position": 1}, {"name": "B", "position": 2}])
        f2 = _frame([{"name": "A", "position": 2}, {"name": "B", "position": 1}])
        events = detect_overtakes([f1, f2])
        for e in events:
            assert hasattr(e, "type")
            assert hasattr(e, "tick")
            assert hasattr(e, "cars")


class TestDetectBattles:
    def test_detect_battle(self):
        frames = []
        for _ in range(100):
            frames.append(_frame([
                {"name": "A", "position": 1, "gap_ahead_s": 0},
                {"name": "B", "position": 2, "gap_ahead_s": 0.8},
            ]))
        events = detect_battles(frames, 30)
        assert any(e.type == "BATTLE" for e in events)

    def test_no_battle_when_gap_large(self):
        frames = []
        for _ in range(100):
            frames.append(_frame([
                {"name": "A", "position": 1, "gap_ahead_s": 0},
                {"name": "B", "position": 2, "gap_ahead_s": 5.0},
            ]))
        events = detect_battles(frames, 30)
        assert not any(e.type == "BATTLE" for e in events)


class TestDetectIncidents:
    def test_detect_spin(self):
        f1 = _frame([{"name": "A", "in_spin": False}])
        f2 = _frame([{"name": "A", "in_spin": True}])
        events = detect_incidents([f1, f2])
        assert any(e.type == "SPIN" for e in events)

    def test_detect_safety_car(self):
        f1 = _frame([{"name": "A", "safety_car": False}])
        f2 = _frame([{"name": "A", "safety_car": True}])
        events = detect_incidents([f1, f2])
        assert any(e.type == "SAFETY_CAR" for e in events)


class TestDetectPitStops:
    def test_detect_pit_stop(self):
        f1 = _frame([{"name": "A", "pit_status": "racing"}])
        f2 = _frame([{"name": "A", "pit_status": "pit_entry"}])
        events = detect_pit_stops([f1, f2])
        assert any(e.type == "PIT_STOP" for e in events)


class TestDetectFastestLap:
    def test_detect_fastest_lap(self):
        results = [{"name": "A", "best_lap_s": 55.0}, {"name": "B", "best_lap_s": 56.0}]
        events = detect_fastest_laps(results)
        assert any(e.type == "FASTEST_LAP" for e in events)
        assert events[0].cars == ["A"]


class TestDetectEvents:
    def test_events_chronological(self):
        f1 = _frame([{"name": "A", "position": 1, "in_spin": False},
                      {"name": "B", "position": 2}])
        f2 = _frame([{"name": "A", "position": 2, "in_spin": True},
                      {"name": "B", "position": 1}])
        events = detect_events([f1, f2], ticks_per_sec=30)
        ticks = [e.tick for e in events]
        assert ticks == sorted(ticks)
