"""Tests for simulation v2 physics integration (T3.6).

Validates world_scale, fuel, tire compounds, pit stops, engine modes,
and backward compatibility with old-style strategies.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulation import RaceSim
from engine.replay import _compute_positions
from engine.track_gen import generate_track, interpolate_track
from tracks import get_track


def _default_strategy(s):
    """Default balanced strategy for test cars."""
    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}


def _make_cars(n=3, strategy=None):
    """Create n test cars with optional custom strategy."""
    strat = strategy or _default_strategy
    return [
        {
            "CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}",
            "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
            "strategy": strat,
        }
        for i in range(n)
    ]


def _make_procedural_track():
    control = generate_track(seed=42)
    return interpolate_track(control, resolution=500)


def _make_monaco_track():
    track_data = get_track("monaco")
    return interpolate_track(track_data["control_points"], resolution=500)


# ── Cycle 1: world_scale ────────────────────────────────────────────────────

class TestWorldScale:
    """world_scale is calibrated from track_length / 3333.0."""

    def test_procedural_track_world_scale_calibrated(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=1, seed=42)
        expected = sim.track_length / 3333.0
        assert abs(sim.world_scale - expected) < 0.001

    def test_world_scale_independent_of_real_length(self):
        track = _make_procedural_track()
        sim_none = RaceSim(_make_cars(), track, laps=1, seed=42, real_length_m=None)
        sim_val = RaceSim(_make_cars(), track, laps=1, seed=42, real_length_m=5000)
        assert abs(sim_none.world_scale - sim_val.world_scale) < 0.001

    def test_zero_real_length_same_world_scale(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=1, seed=42, real_length_m=0)
        expected = sim.track_length / 3333.0
        assert abs(sim.world_scale - expected) < 0.001

    def test_monaco_world_scale_calibrated(self):
        track = _make_monaco_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42, real_length_m=3337)
        expected = sim.track_length / 3333.0
        assert abs(sim.world_scale - expected) < 0.001

    def test_world_scale_positive(self):
        track = _make_monaco_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42, real_length_m=3337)
        assert sim.world_scale > 0


# ── Cycle 2: Per-car state fields ────────────────────────────────────────────

class TestCarStateFields:
    """New per-car state fields for fuel, tires, pits, engine mode."""

    def test_tire_compound_default(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42)
        for state in sim.states:
            assert state["tire_compound"] == "medium"

    def test_tire_age_laps_starts_zero(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42)
        for state in sim.states:
            assert state["tire_age_laps"] == 0

    def test_fuel_fields_initialized(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42)
        for state in sim.states:
            assert state["fuel_kg"] > 0
            assert state["max_fuel_kg"] == state["fuel_kg"]
            assert state["fuel_base_rate"] > 0

    def test_pit_state_initialized(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42)
        for state in sim.states:
            assert state["pit_state"]["status"] == "racing"
            assert state["pit_state"]["pit_stops"] == 0

    def test_engine_mode_default(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42)
        for state in sim.states:
            assert state["engine_mode"] == "standard"


# ── Cycle 3: build_strategy_state new fields ─────────────────────────────────

class TestStrategyStateFields:
    """build_strategy_state exposes fuel, tire, engine, pit info."""

    def _build_state(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(), track, laps=3, seed=42)
        positions = _compute_positions(sim.states)
        return sim.build_strategy_state(sim.states[0], positions)

    def test_fuel_remaining_in_strategy_state(self):
        ss = self._build_state()
        assert "fuel_remaining" in ss
        assert ss["fuel_remaining"] > 0

    def test_fuel_pct_in_strategy_state(self):
        ss = self._build_state()
        assert "fuel_pct" in ss
        assert 0.0 <= ss["fuel_pct"] <= 1.0

    def test_tire_compound_in_strategy_state(self):
        ss = self._build_state()
        assert ss["tire_compound"] == "medium"

    def test_engine_mode_in_strategy_state(self):
        ss = self._build_state()
        assert ss["engine_mode"] == "standard"

    def test_pit_status_in_strategy_state(self):
        ss = self._build_state()
        assert ss["pit_status"] == "racing"
        assert ss["pit_stops"] == 0

    def test_gap_fields_in_strategy_state(self):
        ss = self._build_state()
        assert "gap_ahead_s" in ss
        assert "gap_behind_s" in ss


# ── Cycle 4: Fuel decreases over race ────────────────────────────────────────

class TestFuelConsumption:
    """Fuel decreases during simulation steps."""

    def test_fuel_decreases_after_steps(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(2), track, laps=3, seed=42)
        starting_fuel = sim.states[0]["fuel_kg"]
        for _ in range(300):
            sim.step()
        assert sim.states[0]["fuel_kg"] < starting_fuel

    def test_fuel_never_negative(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(2), track, laps=1, seed=42)
        sim.run()
        for state in sim.states:
            assert state["fuel_kg"] >= 0.0


# ── Cycle 5: Tire compound integration ───────────────────────────────────────

class TestTireCompoundIntegration:
    """Tire wear uses compound model from tire_model."""

    def test_tire_wear_increases(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(2), track, laps=1, seed=42)
        for _ in range(300):
            sim.step()
        assert sim.states[0]["tire_wear"] > 0.0

    def test_tire_compound_preserved_during_race(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(2), track, laps=1, seed=42)
        for _ in range(100):
            sim.step()
        assert sim.states[0]["tire_compound"] == "medium"


# ── Cycle 6: Engine mode affects speed ────────────────────────────────────────

class TestEngineMode:
    """Engine mode influences top speed via power multiplier."""

    def test_push_mode_faster_than_standard(self):
        track = _make_procedural_track()
        push_cars = _make_cars(2, strategy=lambda s: {
            "throttle": 1.0, "boost": False, "tire_mode": "balanced",
            "engine_mode": "push",
        })
        std_cars = _make_cars(2, strategy=lambda s: {
            "throttle": 1.0, "boost": False, "tire_mode": "balanced",
            "engine_mode": "standard",
        })
        sim_push = RaceSim(push_cars, track, laps=1, seed=42)
        sim_std = RaceSim(std_cars, track, laps=1, seed=42)
        for _ in range(300):
            sim_push.step()
            sim_std.step()
        assert sim_push.states[0]["distance"] > sim_std.states[0]["distance"]

    def test_conserve_mode_slower_than_standard(self):
        track = _make_procedural_track()
        conserve_cars = _make_cars(2, strategy=lambda s: {
            "throttle": 1.0, "boost": False, "tire_mode": "balanced",
            "engine_mode": "conserve",
        })
        std_cars = _make_cars(2, strategy=lambda s: {
            "throttle": 1.0, "boost": False, "tire_mode": "balanced",
            "engine_mode": "standard",
        })
        sim_con = RaceSim(conserve_cars, track, laps=1, seed=42)
        sim_std = RaceSim(std_cars, track, laps=1, seed=42)
        for _ in range(300):
            sim_con.step()
            sim_std.step()
        assert sim_con.states[0]["distance"] < sim_std.states[0]["distance"]


# ── Cycle 7: Pit stop wiring ─────────────────────────────────────────────────

class TestPitStopWiring:
    """Pit requests from strategy trigger pit state machine."""

    def test_pit_request_enters_pit(self):
        pit_requested = [False]

        def pit_strategy(s):
            result = {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
            if s["lap"] >= 1 and not pit_requested[0]:
                result["pit_request"] = True
                result["tire_compound_request"] = "soft"
                pit_requested[0] = True
            return result

        track = _make_procedural_track()
        cars = _make_cars(2, strategy=pit_strategy)
        sim = RaceSim(cars, track, laps=3, seed=42)
        for _ in range(20000):
            sim.step()
            if pit_requested[0]:
                break
        for _ in range(10):
            sim.step()
        any_in_pit = any(
            s["pit_state"]["status"] != "racing" for s in sim.states
        )
        assert pit_requested[0], "Pit was never requested"
        assert any_in_pit or any(
            s["pit_state"]["pit_stops"] > 0 for s in sim.states
        )


# ── Cycle 8: Distance update with world_scale ────────────────────────────────

class TestDistanceWithWorldScale:
    """Distance advancement uses world_scale and m/s conversion."""

    def test_monaco_lap_time_reasonable(self):
        """Monaco lap should take 30-180 seconds at race pace."""
        track_data = get_track("monaco")
        track = interpolate_track(track_data["control_points"], resolution=500)
        cars = _make_cars(2)
        sim = RaceSim(cars, track, laps=2, seed=42, real_length_m=3337)
        ticks_to_lap = 0
        for _ in range(20000):
            sim.step()
            ticks_to_lap += 1
            if any(s["lap"] >= 1 for s in sim.states):
                break
        lap_time_seconds = ticks_to_lap / sim.TICKS_PER_SEC
        assert 30 <= lap_time_seconds <= 180, (
            f"Monaco lap time {lap_time_seconds:.1f}s is unreasonable"
        )

    def test_tire_age_laps_increments(self):
        track = _make_procedural_track()
        sim = RaceSim(_make_cars(2), track, laps=3, seed=42)
        sim.run()
        assert any(s["tire_age_laps"] > 0 for s in sim.states)

    def test_pit_stationary_no_distance(self):
        """Car should not advance distance while pit_stationary."""
        track = _make_procedural_track()
        cars = _make_cars(2)
        sim = RaceSim(cars, track, laps=3, seed=42)
        sim.states[0]["pit_state"]["status"] = "pit_stationary"
        sim.states[0]["pit_state"]["pit_timer"] = 100
        dist_before = sim.states[0]["distance"]
        sim.step()
        assert sim.states[0]["distance"] == dist_before


# ── Cycle 9: Backward compatibility ──────────────────────────────────────────

class TestBackwardCompat:
    """Old-style strategies still work with new simulation."""

    def test_old_strategy_works(self):
        """Strategy returning only throttle/boost/tire_mode still works."""
        old_cars = _make_cars(2, strategy=lambda s: {
            "throttle": 0.8, "boost": False, "tire_mode": "push",
        })
        track = _make_procedural_track()
        sim = RaceSim(old_cars, track, laps=1, seed=42)
        results = sim.run()
        assert all(r["finished"] for r in results)

    def test_empty_dict_strategy_works(self):
        empty_cars = _make_cars(2, strategy=lambda s: {})
        track = _make_procedural_track()
        sim = RaceSim(empty_cars, track, laps=1, seed=42)
        results = sim.run()
        assert all(r["finished"] for r in results)

    def test_none_strategy_works(self):
        none_cars = _make_cars(2, strategy=lambda s: None)
        track = _make_procedural_track()
        sim = RaceSim(none_cars, track, laps=1, seed=42)
        results = sim.run()
        assert all(r["finished"] for r in results)


# ── Cycle 10: race_runner + exports ──────────────────────────────────────────

class TestRaceRunnerIntegration:
    """race_runner passes real_length_m to RaceSim."""

    def test_named_track_has_world_scale(self, tmp_path):
        """run_race with named track produces valid output."""
        from engine.race_runner import run_race
        for i in range(2):
            (tmp_path / f"car{i}.py").write_text(
                f'CAR_NAME = "Car{i}"\nCAR_COLOR = "#FF000{i}"\n'
                f'POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n'
            )
        output = tmp_path / "replay.json"
        run_race(car_dir=str(tmp_path), laps=1, track_seed=42,
                 output=str(output), track_name="monaco")
        assert output.exists()


class TestNewExports:
    """engine/__init__.py exports new modules."""

    def test_tire_model_exports(self):
        from engine import get_compound, compute_grip_multiplier, get_compound_names
        assert callable(get_compound)
        assert callable(compute_grip_multiplier)
        assert isinstance(get_compound_names(), list)

    def test_fuel_model_exports(self):
        from engine import get_engine_mode, get_engine_mode_names
        assert callable(get_engine_mode)
        assert isinstance(get_engine_mode_names(), list)

    def test_pit_lane_exports(self):
        from engine import create_pit_state, is_in_pit
        state = create_pit_state()
        assert not is_in_pit(state)


# ── Cycle 11: Tier 2 simulation integration (T5.4) ──────────────────────────

def _make_monza_track():
    track_data = get_track("monza")
    return interpolate_track(track_data["control_points"], resolution=500)


def _make_cars_with_setup(n=3, strategy=None):
    """Create test cars that have setup and setup_raw like car_loader produces."""
    from engine.setup_model import validate_setup, apply_setup
    strat = strategy or _default_strategy
    cars = []
    for i in range(n):
        stats = {"power": 0.5, "grip": 0.5, "weight": 0.5, "aero": 0.5, "brakes": 0.5}
        raw = validate_setup({})
        setup = apply_setup(stats, raw)
        cars.append({
            "CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}",
            "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
            "strategy": strat,
            "setup_raw": raw,
            "setup": setup,
        })
    return cars


class TestTier2Simulation:
    """Tier 2 integration: tire temp, DRS, setup in simulation."""

    def test_tire_temp_exposed_in_strategy_state(self):
        """After 1 tick, strategy state has 'tire_temp' as a float."""
        track = _make_procedural_track()
        cars = _make_cars_with_setup(2)
        sim = RaceSim(cars, track, laps=1, seed=42)
        sim.step()
        positions = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], positions)
        assert "tire_temp" in ss
        assert isinstance(ss["tire_temp"], float)

    def test_tire_temp_rises_from_cold_start(self):
        """After 300 ticks, tire_temp > 20.0 for at least one car."""
        track = _make_procedural_track()
        cars = _make_cars_with_setup(2)
        sim = RaceSim(cars, track, laps=3, seed=42)
        for _ in range(300):
            sim.step()
        assert any(s["tire_temp"] > 20.0 for s in sim.states)

    def test_drs_state_exposed_in_strategy_state(self):
        """Strategy state has drs_available (bool) and in_drs_zone (bool)."""
        track = _make_procedural_track()
        cars = _make_cars_with_setup(2)
        sim = RaceSim(cars, track, laps=1, seed=42)
        sim.step()
        positions = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], positions)
        assert "drs_available" in ss
        assert isinstance(ss["drs_available"], bool)
        assert "in_drs_zone" in ss
        assert isinstance(ss["in_drs_zone"], bool)

    def test_drs_active_on_monza(self):
        """On monza with DRS zones, at least 1 replay frame has drs_active=True."""
        track = _make_monza_track()
        drs_zones = get_track("monza").get("drs_zones", [])

        def drs_strategy(s):
            return {"throttle": 1.0, "boost": False, "tire_mode": "balanced",
                    "drs_request": True}

        cars = _make_cars_with_setup(3, strategy=drs_strategy)
        sim = RaceSim(cars, track, laps=2, seed=42, track_name="monza",
                      drs_zones=drs_zones)
        sim.run()
        replay = sim.export_replay()
        found_drs = False
        for frame in replay["frames"]:
            for car_frame in frame:
                if car_frame.get("drs_active", False):
                    found_drs = True
                    break
            if found_drs:
                break
        assert found_drs, "No frame had drs_active=True on monza"

    def test_current_setup_exposed_in_strategy_state(self):
        """Strategy state has 'current_setup' dict."""
        track = _make_procedural_track()
        cars = _make_cars_with_setup(2)
        sim = RaceSim(cars, track, laps=1, seed=42)
        sim.step()
        positions = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], positions)
        assert "current_setup" in ss
        assert isinstance(ss["current_setup"], dict)

    def test_backward_compat_no_setup_still_runs(self):
        """Cars without setup_raw/setup attributes race cleanly."""
        track = _make_procedural_track()
        cars = _make_cars(2)  # No setup keys
        sim = RaceSim(cars, track, laps=1, seed=42)
        results = sim.run()
        assert all(r["finished"] for r in results)

    def test_backward_compat_no_drs_request_still_works(self):
        """Strategy returning no drs_request key works fine."""
        track = _make_monza_track()
        drs_zones = get_track("monza").get("drs_zones", [])
        cars = _make_cars(2)  # default strategy has no drs_request
        sim = RaceSim(cars, track, laps=1, seed=42, drs_zones=drs_zones)
        results = sim.run()
        assert all(r["finished"] for r in results)

    def test_tire_temp_in_replay_frames(self):
        """All replay frames have 'tire_temp' key for each car."""
        track = _make_procedural_track()
        cars = _make_cars_with_setup(2)
        sim = RaceSim(cars, track, laps=1, seed=42)
        sim.run()
        replay = sim.export_replay()
        for frame in replay["frames"]:
            for car_frame in frame:
                assert "tire_temp" in car_frame
