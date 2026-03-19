"""Tests for opponent visibility model (T12.1)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.visibility import (
    OBSERVABLE_FIELDS, PRIVATE_FIELDS, build_opponent_info, filter_nearby_cars,
)


def _mock_states():
    """Create minimal car states for testing."""
    return [
        {"car_idx": 0, "name": "CarA", "speed": 200.0, "distance": 500.0,
         "lateral": 0.1, "lap": 2, "tire_compound": "soft", "tire_age_laps": 5,
         "tire_wear": 0.3, "fuel_kg": 50.0, "tire_temp": 85.0, "damage": {"damage": 0.1},
         "engine_mode": "push", "ers": {"energy": 3.5}, "ers_deploy_mode": "attack",
         "brake_state": {"temp": 400.0}, "spin_recovery": 0, "contact_cooldown": 0,
         "finished": False, "finish_tick": None, "pit_state": {"status": "racing", "pit_stops": 1},
         "drs_active": True, "boost_available": True, "boost_active": 0},
        {"car_idx": 1, "name": "CarB", "speed": 195.0, "distance": 480.0,
         "lateral": -0.2, "lap": 2, "tire_compound": "medium", "tire_age_laps": 10,
         "tire_wear": 0.5, "fuel_kg": 40.0, "tire_temp": 90.0, "damage": {"damage": 0.2},
         "engine_mode": "conserve", "ers": {"energy": 2.0}, "ers_deploy_mode": "harvest",
         "brake_state": {"temp": 500.0}, "spin_recovery": 0, "contact_cooldown": 0,
         "finished": False, "finish_tick": None, "pit_state": {"status": "racing", "pit_stops": 0},
         "drs_active": False, "boost_available": False, "boost_active": 0},
    ]


class TestBuildOpponentInfo:
    def test_opponent_info_has_observable_fields(self):
        states = _mock_states()
        positions = {0: 1, 1: 2}
        result = build_opponent_info(states, 0, positions, {}, 30, 100)
        assert len(result) == 1  # excludes self
        opp = result[0]
        for field in ["name", "position", "speed", "lateral", "tire_compound",
                       "tire_age_laps", "pit_stops", "drs_active", "in_spin",
                       "finished", "lap"]:
            assert field in opp, f"Missing observable field: {field}"

    def test_opponent_info_missing_private_fields(self):
        states = _mock_states()
        positions = {0: 1, 1: 2}
        result = build_opponent_info(states, 0, positions, {}, 30, 100)
        opp = result[0]
        for field in ["tire_wear", "fuel_remaining", "fuel_pct", "tire_temp",
                       "engine_mode", "damage", "ers_energy", "ers_deploy_mode",
                       "brake_temp", "spin_risk"]:
            assert field not in opp, f"Private field leaked: {field}"

    def test_opponent_info_excludes_self(self):
        states = _mock_states()
        positions = {0: 1, 1: 2}
        result = build_opponent_info(states, 0, positions, {}, 30, 100)
        names = [o["name"] for o in result]
        assert "CarA" not in names
        assert "CarB" in names


class TestFilterNearbyCars:
    def test_nearby_cars_filtered(self):
        nearby = [{"name": "CarB", "distance_ahead": 20.0, "speed": 195.0,
                    "lateral": -0.2, "tire_compound": "medium", "tire_age_laps": 10,
                    "tire_wear": 0.5, "fuel_pct": 0.8}]
        filtered = filter_nearby_cars(nearby)
        assert len(filtered) == 1
        assert "tire_wear" not in filtered[0]
        assert "fuel_pct" not in filtered[0]
        assert filtered[0]["name"] == "CarB"
        assert filtered[0]["speed"] == 195.0


class TestFieldSets:
    def test_observable_fields_complete(self):
        expected = {"name", "position", "speed", "lateral", "tire_compound",
                     "tire_age_laps", "pit_stops", "drs_active", "in_spin",
                     "finished", "gap_ahead_s", "lap"}
        assert expected.issubset(OBSERVABLE_FIELDS)

    def test_private_fields_complete(self):
        expected = {"tire_wear", "fuel_remaining", "fuel_pct", "tire_temp",
                     "engine_mode", "damage", "ers_energy", "ers_deploy_mode",
                     "brake_temp", "spin_risk", "dirty_air_factor",
                     "boost_available", "boost_active"}
        assert expected.issubset(PRIVATE_FIELDS)
