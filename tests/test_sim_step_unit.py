"""Unit tests for engine/sim_step.py — per-car step helpers.

Tests build_strategy_state dict structure and _resolve_decision parsing.
step_car is deeply coupled to the sim, so not unit-tested here.
"""

from engine.sim_step import VALID_ENGINE_MODES, build_strategy_state
from engine.timing import CarTiming
from engine.track_gen import (
    CurvatureLookup,
    compute_track_data,
    generate_track,
    interpolate_track,
)


def _make_curvature_lookup():
    control = generate_track(seed=1, num_points=6)
    track = interpolate_track(control, resolution=120)
    dists, curvs, length = compute_track_data(track)
    return CurvatureLookup(dists, curvs, length), length


def _make_car_state(car_idx=0, name="TestCar", distance=50.0):
    """Minimal car state dict with all fields build_strategy_state reads."""
    return {
        "car_idx": car_idx,
        "name": name,
        "speed": 80.0,
        "distance": distance,
        "lateral": 0.0,
        "lap": 1,
        "tire_wear": 0.1,
        "boost_available": True,
        "boost_active": 0,
        "fuel_kg": 50.0,
        "max_fuel_kg": 100.0,
        "tire_compound": "medium",
        "tire_age_laps": 3,
        "engine_mode": "standard",
        "pit_state": {"status": "racing", "pit_stops": 0},
        "tire_temp": 90.0,
        "drs_available": False,
        "drs_active": False,
        "_in_drs_zone": False,
        "setup_raw": {},
        "_in_dirty_air": False,
        "_dirty_air_grip": 1.0,
        "damage": {"damage": 0.0},
        "_spin_risk": 0.0,
        "spin_recovery": 0,
        "ers": {"energy": 4.0},
        "ers_deploy_mode": "balanced",
        "brake_state": {"temp": 300.0},
    }


class TestBuildStrategyState:
    """Tests for build_strategy_state return value structure."""

    def _build(self):
        lookup, length = _make_curvature_lookup()
        cs = _make_car_state(distance=50.0)
        other = _make_car_state(car_idx=1, name="Rival", distance=120.0)
        all_states = [cs, other]
        timings = {
            "TestCar": CarTiming("TestCar"),
            "Rival": CarTiming("Rival"),
        }
        positions = {0: 2, 1: 1}
        safety_car_state = {"status": "inactive", "laps_remaining": 0}
        weather_state = {"wetness": 0.0, "state": "dry"}
        result = build_strategy_state(
            car_state=cs,
            all_states=all_states,
            timings=timings,
            tick=30,
            ticks_per_sec=30,
            distances=[0.0, length],
            curvature_lookup=lookup,
            track_length=length,
            sector_boundaries=(0.333, 0.666, 1.0),
            world_scale=1.0,
            track_name="test_track",
            car_data_dir=None,
            race_number=1,
            total_laps=5,
            drs_zones=[],
            safety_car_state=safety_car_state,
            weather_state=weather_state,
            weather_forecast=[],
            positions=positions,
        )
        return result

    def test_returns_dict(self):
        result = self._build()
        assert isinstance(result, dict)

    def test_contains_core_keys(self):
        result = self._build()
        required_keys = [
            "speed", "position", "total_cars", "lap", "total_laps",
            "tire_wear", "boost_available", "boost_active",
            "curvature", "distance", "track_length", "lateral",
            "fuel_remaining", "fuel_pct", "tire_compound",
            "engine_mode", "pit_status", "gap_ahead_s", "gap_behind_s",
            "track_name", "race_number", "tire_temp",
            "drs_available", "drs_active", "damage",
            "safety_car", "ers_energy", "brake_temp",
            "weather_state", "opponent_info",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_position_and_total_cars(self):
        result = self._build()
        assert result["position"] == 2  # car_idx=0 is P2 per positions dict
        assert result["total_cars"] == 2

    def test_fuel_pct_range(self):
        result = self._build()
        assert 0.0 <= result["fuel_pct"] <= 1.0

    def test_elapsed_s_correct(self):
        result = self._build()
        # tick=30, ticks_per_sec=30 -> 1.0s
        assert result["elapsed_s"] == 1.0


class TestValidEngineModes:
    """Tests for engine mode validation constant."""

    def test_valid_modes_include_standard(self):
        assert "standard" in VALID_ENGINE_MODES

    def test_valid_modes_include_push_and_conserve(self):
        assert "push" in VALID_ENGINE_MODES
        assert "conserve" in VALID_ENGINE_MODES
