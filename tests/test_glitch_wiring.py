"""Tests for glitch wiring into the race loop (T27.7)."""

import random

from engine.safe_call import _apply_glitch
from engine.glitch import GlitchEngine
from engine.parts_api import get_defaults
from engine.efficiency_engine import run_efficiency_tick
from engine.parts_runner import create_initial_state
from engine.parts_api import get_hardware_spec


class TestApplyGlitch:
    """Unit tests for the _apply_glitch helper in safe_call."""

    def test_no_glitch_engine_returns_entry_unchanged(self):
        """When glitch_ctx is None, entry should pass through unchanged."""
        entry = {"part": "engine_map", "tick": 0, "output": (0.9, 0.9),
                 "status": "ok", "efficiency": 1.0}
        defaults = get_defaults()
        result = _apply_glitch(entry, "engine_map", (10000, 1.0, 90),
                               defaults["engine_map"], None)
        assert result["status"] == "ok"
        assert result["output"] == (0.9, 0.9)

    def test_error_status_skipped(self):
        """Glitch check should not apply to entries with error/timeout status."""
        ge = GlitchEngine(reliability_scale=1.0)
        ctx = {"engine": ge, "reliability": 0.0, "car_idx": 0,
               "rng": random.Random(1)}
        entry = {"part": "engine_map", "tick": 0, "output": None,
                 "status": "error", "efficiency": 0.85}
        defaults = get_defaults()
        result = _apply_glitch(entry, "engine_map", (10000, 1.0, 90),
                               defaults["engine_map"], ctx)
        assert result["status"] == "error"

    def test_glitch_replaces_output_with_default(self):
        """When reliability is 0 (worst), glitch should fire and replace output."""
        ge = GlitchEngine(reliability_scale=1.0)
        rng = random.Random(42)
        ctx = {"engine": ge, "reliability": 0.0, "car_idx": 0, "rng": rng}
        entry = {"part": "engine_map", "tick": 5, "output": (0.5, 0.5),
                 "status": "ok", "efficiency": 1.0}
        defaults = get_defaults()
        result = _apply_glitch(entry, "engine_map", (10000, 1.0, 90),
                               defaults["engine_map"], ctx)
        assert result["status"] == "glitch"
        expected = defaults["engine_map"](10000, 1.0, 90)
        assert result["output"] == expected

    def test_active_glitch_persists(self):
        """If already glitching, should keep glitch status."""
        ge = GlitchEngine(reliability_scale=0.3)
        ge.set_active_glitch("gearbox", 0, 10)
        ctx = {"engine": ge, "reliability": 1.0, "car_idx": 0,
               "rng": random.Random(1)}
        entry = {"part": "gearbox", "tick": 5, "output": 5,
                 "status": "ok", "efficiency": 1.0}
        defaults = get_defaults()
        result = _apply_glitch(entry, "gearbox",
                               (10000, 200, 5, 1.0),
                               defaults["gearbox"], ctx)
        assert result["status"] == "glitch"

    def test_perfect_reliability_no_glitch(self):
        """Reliability 1.0 should never trigger new glitches."""
        ge = GlitchEngine(reliability_scale=0.3)
        rng = random.Random(42)
        ctx = {"engine": ge, "reliability": 1.0, "car_idx": 0, "rng": rng}
        entry = {"part": "cooling", "tick": 0, "output": 0.3,
                 "status": "ok", "efficiency": 1.0}
        defaults = get_defaults()
        for tick in range(100):
            e = dict(entry)
            e["tick"] = tick
            result = _apply_glitch(e, "cooling",
                                   (90, 400, 30, 200),
                                   defaults["cooling"], ctx)
            assert result["status"] == "ok", f"Glitched at tick {tick}"


def _make_state_and_hw():
    """Helper: create a minimal car state and hardware spec for tick tests."""
    hw = {**get_hardware_spec("ENGINE_SPEC", "v6_1000hp"),
          **get_hardware_spec("AERO_SPEC", "medium_downforce"),
          **get_hardware_spec("CHASSIS_SPEC", "standard")}
    state = create_initial_state(hw)
    state["speed_kmh"] = 200
    state["gear"] = 5
    state["position"] = 1
    state["gap_ahead"] = 0
    state["laps_total"] = 3
    state["lap"] = 0
    return state, hw


class TestEfficiencyTickGlitch:
    """Tests for glitch params wired through run_efficiency_tick."""

    def test_accepts_glitch_params(self):
        """run_efficiency_tick should accept glitch_engine, reliability, car_idx, glitch_rng."""
        state, hw = _make_state_and_hw()
        defaults = get_defaults()
        physics = {"curvature": 0, "corner_phase": "straight",
                   "lateral_g": 0, "bump_severity": 0, "weather_wetness": 0,
                   "throttle_demand": 1.0, "target_speed": 300, "braking": False}
        ge = GlitchEngine(reliability_scale=0.3)
        rng = random.Random(42)
        # Should not raise
        s, log, prod = run_efficiency_tick(
            defaults, state, physics, hw, 1/30, 0,
            glitch_engine=ge, reliability=1.0, car_idx=0, glitch_rng=rng)
        assert isinstance(s, dict)
        assert isinstance(log, list)

    def test_zero_reliability_produces_glitches(self):
        """With reliability=0 and high scale, some parts should glitch."""
        state, hw = _make_state_and_hw()
        defaults = get_defaults()
        physics = {"curvature": 0, "corner_phase": "straight",
                   "lateral_g": 0, "bump_severity": 0, "weather_wetness": 0,
                   "throttle_demand": 1.0, "target_speed": 300, "braking": False}
        ge = GlitchEngine(reliability_scale=1.0)  # max scale
        rng = random.Random(42)
        glitch_count = 0
        for tick in range(50):
            s, log, prod = run_efficiency_tick(
                defaults, state, physics, hw, 1/30, tick,
                glitch_engine=ge, reliability=0.0, car_idx=0, glitch_rng=rng)
            glitch_count += sum(1 for e in log if e["status"] == "glitch")
            state = s
        assert glitch_count > 0, "Expected at least one glitch with 0 reliability"

    def test_tick_glitches_called(self):
        """After a tick, active glitch durations should decrease."""
        state, hw = _make_state_and_hw()
        defaults = get_defaults()
        physics = {"curvature": 0, "corner_phase": "straight",
                   "lateral_g": 0, "bump_severity": 0, "weather_wetness": 0,
                   "throttle_demand": 1.0, "target_speed": 300, "braking": False}
        ge = GlitchEngine(reliability_scale=0.3)
        ge.set_active_glitch("engine_map", 0, 5)
        rng = random.Random(1)
        run_efficiency_tick(
            defaults, state, physics, hw, 1/30, 0,
            glitch_engine=ge, reliability=1.0, car_idx=0, glitch_rng=rng)
        # Duration should have decreased by 1 (from 5 to 4)
        assert ge._active[0]["engine_map"] == 4


class TestPartsRaceSimGlitch:
    """Tests for GlitchEngine + reliability on PartsRaceSim."""

    def test_glitch_engine_exists(self):
        """PartsRaceSim should have a glitch_engine attribute."""
        from engine.car_loader import load_all_cars
        from engine.parts_simulation import PartsRaceSim
        from tracks import get_track
        from engine.track_gen import interpolate_track
        td = get_track("monza")
        pts = interpolate_track(td["control_points"], resolution=500)
        cars = load_all_cars("cars")
        sim = PartsRaceSim(cars, pts, laps=1, seed=42, track_name="monza",
                           real_length_m=td.get("real_length_m"))
        assert hasattr(sim, "glitch_engine")
        assert isinstance(sim.glitch_engine, GlitchEngine)

    def test_car_reliability_defaults_to_one(self):
        """Cars without _source should have reliability 1.0."""
        from engine.parts_simulation import PartsRaceSim
        from tracks import get_track
        from engine.track_gen import interpolate_track
        td = get_track("monza")
        pts = interpolate_track(td["control_points"], resolution=500)
        # Minimal cars without _source
        cars = [{"CAR_NAME": "TestCar", "CAR_COLOR": "#ff0000"}]
        sim = PartsRaceSim(cars, pts, laps=1, seed=42, track_name="monza",
                           real_length_m=td.get("real_length_m"))
        assert hasattr(sim, "car_reliability")
        assert sim.car_reliability == [1.0]

    def test_car_reliability_computed_from_source(self):
        """Cars with _source should have reliability computed from code quality."""
        from engine.parts_simulation import PartsRaceSim
        from engine.code_quality import compute_reliability_score
        from tracks import get_track
        from engine.track_gen import interpolate_track
        td = get_track("monza")
        pts = interpolate_track(td["control_points"], resolution=500)
        source = "def engine_map(rpm, throttle, temp):\n    return (1.0, 1.0)\n"
        cars = [{"CAR_NAME": "TestCar", "CAR_COLOR": "#ff0000",
                 "_source": source}]
        sim = PartsRaceSim(cars, pts, laps=1, seed=42, track_name="monza",
                           real_length_m=td.get("real_length_m"))
        expected = compute_reliability_score(source)
        assert sim.car_reliability[0] == expected
