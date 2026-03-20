"""Sprint 20 integration gate — your code drives a car on Monza (T20.6)."""

import pathlib

import pytest

from engine.parts_api import get_defaults, HARDWARE_SPECS, CAR_PARTS
from engine.parts_runner import create_initial_state, run_parts_tick

pytestmark = pytest.mark.slow


def _run_laps(n_ticks=3000):
    """Run default car for n_ticks and return final state + logs."""
    specs = HARDWARE_SPECS["ENGINE_SPEC"]["v6_1000hp"]
    chassis = HARDWARE_SPECS["CHASSIS_SPEC"]["standard"]
    hw = {**specs, **chassis}
    state = create_initial_state(hw)
    defaults = get_defaults()
    all_logs = []
    for tick in range(n_ticks):
        physics = {"curvature": 0.02 if (tick % 300) > 200 else 0.001,
                    "corner_phase": "mid" if (tick % 300) > 200 else "straight",
                    "lateral_g": 1.5 if (tick % 300) > 200 else 0.1,
                    "bump_severity": 0.0, "weather_wetness": 0.0,
                    "throttle_demand": 1.0, "braking": (tick % 300) > 180 and (tick % 300) < 210}
        state, log = run_parts_tick(defaults, state, physics, hw, 1/30, tick)
        all_logs.extend(log)
    return state, all_logs


class TestPartsRace:
    def test_race_completes_with_defaults(self):
        state, _ = _run_laps(1000)
        assert state["speed_kmh"] > 0

    def test_speed_varies(self):
        """Speed should change — not stuck at one value."""
        specs = HARDWARE_SPECS["ENGINE_SPEC"]["v6_1000hp"]
        chassis = HARDWARE_SPECS["CHASSIS_SPEC"]["standard"]
        hw = {**specs, **chassis}
        state = create_initial_state(hw)
        defaults = get_defaults()
        speeds = []
        for tick in range(500):
            curv = 0.08 if (tick % 200) > 150 else 0.001
            physics = {"curvature": curv, "corner_phase": "mid" if curv > 0.01 else "straight",
                        "lateral_g": 2.0 if curv > 0.01 else 0.1, "bump_severity": 0,
                        "weather_wetness": 0, "throttle_demand": 1.0,
                        "braking": curv > 0.01}
            state, _ = run_parts_tick(defaults, state, physics, hw, 1/30, tick)
            speeds.append(state["speed_kmh"])
        assert max(speeds) > min(speeds) + 20, f"Speed barely varies: {min(speeds):.0f}-{max(speeds):.0f}"

    def test_gearbox_shifts(self):
        state, logs = _run_laps(3000)
        gear_outputs = [entry["output"] for entry in logs if entry["part"] == "gearbox"]
        gears_used = set(gear_outputs)
        assert len(gears_used) >= 2, f"Only used gears: {gears_used}"

    def test_fuel_decreases(self):
        specs = HARDWARE_SPECS["ENGINE_SPEC"]["v6_1000hp"]
        chassis = HARDWARE_SPECS["CHASSIS_SPEC"]["standard"]
        hw = {**specs, **chassis}
        state = create_initial_state(hw)
        start_fuel = state["fuel_remaining_kg"]
        defaults = get_defaults()
        for tick in range(300):
            physics = {"curvature": 0.001, "corner_phase": "straight", "lateral_g": 0.1,
                        "bump_severity": 0, "weather_wetness": 0, "throttle_demand": 1.0,
                        "braking": False}
            state, _ = run_parts_tick(defaults, state, physics, hw, 1/30, tick)
        assert state["fuel_remaining_kg"] < start_fuel

    def test_engine_temp_fluctuates(self):
        state, logs = _run_laps(500)
        assert state["engine_temp"] > 80, "Engine should heat up"

    def test_call_log_has_all_10_parts(self):
        _, logs = _run_laps(100)
        parts_seen = {entry["part"] for entry in logs}
        for part in CAR_PARTS:
            assert part in parts_seen, f"Part {part} never called"


class TestPhysicsRealism:
    def test_top_speed_realistic(self):
        """Default car shouldn't exceed ~350 km/h."""
        state, _ = _run_laps(2000)
        assert state["speed_kmh"] <= 400, f"Speed {state['speed_kmh']} too high"

    def test_acceleration_exists(self):
        """Car should accelerate from standstill."""
        specs = HARDWARE_SPECS["ENGINE_SPEC"]["v6_1000hp"]
        chassis = HARDWARE_SPECS["CHASSIS_SPEC"]["standard"]
        hw = {**specs, **chassis}
        state = create_initial_state(hw)
        defaults = get_defaults()
        for tick in range(300):
            physics = {"curvature": 0.001, "corner_phase": "straight", "lateral_g": 0.1,
                        "bump_severity": 0, "weather_wetness": 0, "throttle_demand": 1.0,
                        "braking": False}
            state, _ = run_parts_tick(defaults, state, physics, hw, 1/30, tick)
        assert state["speed_kmh"] > 10, f"Only reached {state['speed_kmh']:.0f} km/h after 300 ticks"


class TestArchCompliance:
    def test_parts_api_under_limits(self):
        lines = len(pathlib.Path("engine/parts_api.py").read_text().splitlines())
        assert lines <= 250, f"parts_api.py has {lines} lines"

    def test_powertrain_under_limits(self):
        lines = len(pathlib.Path("engine/powertrain_physics.py").read_text().splitlines())
        assert lines <= 150, f"powertrain_physics.py has {lines} lines"

    def test_chassis_under_limits(self):
        lines = len(pathlib.Path("engine/chassis_physics.py").read_text().splitlines())
        assert lines <= 150, f"chassis_physics.py has {lines} lines"

    def test_hybrid_under_limits(self):
        lines = len(pathlib.Path("engine/hybrid_physics.py").read_text().splitlines())
        assert lines <= 150, f"hybrid_physics.py has {lines} lines"
