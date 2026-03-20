"""Tests for the parts runner — sandbox that runs car part functions."""

from engine.parts_api import get_defaults, HARDWARE_SPECS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hardware_specs() -> dict:
    """Standard hardware specs for testing."""
    return {
        "engine": HARDWARE_SPECS["ENGINE_SPEC"]["v6_1000hp"],
        "aero": HARDWARE_SPECS["AERO_SPEC"]["medium_downforce"],
        "chassis": HARDWARE_SPECS["CHASSIS_SPEC"]["standard"],
    }


def _make_physics_state() -> dict:
    """Minimal track/physics state for testing."""
    return {
        "curvature": 0.01,
        "bump_severity": 0.0,
        "weather": "dry",
    }


# ---------------------------------------------------------------------------
# Cycle 1: Basic structure
# ---------------------------------------------------------------------------


class TestCreateInitialState:
    """Test create_initial_state produces a valid car state."""

    def test_create_initial_state_has_required_fields(self):
        from engine.parts_runner import create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)

        required = [
            "speed_kmh", "rpm", "gear", "engine_temp", "brake_temp",
            "battery_temp", "fuel_remaining_kg", "fuel_capacity_kg",
            "tire_wear", "tire_grip", "ers_state", "ride_height",
            "lateral_g", "curvature", "corner_phase", "lap", "laps_total",
            "position", "gap_ahead", "pit_stops", "throttle_demand",
        ]
        for field in required:
            assert field in state, f"Missing field: {field}"

    def test_initial_speed_is_zero(self):
        from engine.parts_runner import create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        assert state["speed_kmh"] == 0

    def test_initial_fuel_matches_capacity(self):
        from engine.parts_runner import create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        assert state["fuel_remaining_kg"] == state["fuel_capacity_kg"]


class TestRunPartsTickReturns:
    """Test run_parts_tick returns the right shape."""

    def test_returns_tuple(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 0.8
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()
        physics = _make_physics_state()

        result = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_state_and_log(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 0.8
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()
        physics = _make_physics_state()

        new_state, call_log = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        assert isinstance(new_state, dict)
        assert isinstance(call_log, list)


# ---------------------------------------------------------------------------
# Cycle 2: Call log completeness
# ---------------------------------------------------------------------------


class TestCallLog:
    """Test that the call log contains entries for all 10 parts."""

    def test_call_log_has_all_parts(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 0.8
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()
        physics = _make_physics_state()

        _, call_log = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        logged_parts = {entry["part"] for entry in call_log}
        expected = {
            "engine_map", "gearbox", "fuel_mix", "suspension", "cooling",
            "brake_bias", "ers_deploy", "ers_harvest", "differential", "strategy",
        }
        assert logged_parts == expected

    def test_log_entries_have_required_fields(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 0.8
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()
        physics = _make_physics_state()

        _, call_log = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        for entry in call_log:
            assert "part" in entry
            assert "tick" in entry
            assert "output" in entry
            assert "status" in entry


# ---------------------------------------------------------------------------
# Cycle 3: Error handling and clamping
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test that broken functions fall back to defaults."""

    def test_error_handling_uses_default(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 0.8
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()

        # Replace gearbox with a broken function
        def broken_gearbox(*_args):
            raise RuntimeError("BOOM")

        parts["gearbox"] = broken_gearbox
        physics = _make_physics_state()

        new_state, call_log = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        gb_entry = [e for e in call_log if e["part"] == "gearbox"][0]
        assert gb_entry["status"] == "error"
        assert "BOOM" in gb_entry["error"]
        # Still got a valid gear (from default)
        assert 1 <= new_state["gear"] <= 8

    def test_clamped_output_logged(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 0.8
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()

        # Return out-of-range cooling effort (should clamp to 0-1)
        def bad_cooling(*_args):
            return 5.0

        parts["cooling"] = bad_cooling
        physics = _make_physics_state()

        _, call_log = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        cool_entry = [e for e in call_log if e["part"] == "cooling"][0]
        assert cool_entry["status"] == "clamped"
        assert cool_entry["output"] == 1.0  # clamped to max


# ---------------------------------------------------------------------------
# Cycle 4: Physics integration
# ---------------------------------------------------------------------------


class TestPhysicsIntegration:
    """Test that physics actually changes state."""

    def test_speed_changes_after_tick(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 1.0
        state["speed_kmh"] = 100.0
        state["gear"] = 4
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()
        physics = _make_physics_state()

        new_state, _ = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        assert new_state["speed_kmh"] != state["speed_kmh"]

    def test_fuel_decreases_after_tick(self):
        from engine.parts_runner import run_parts_tick, create_initial_state

        hw = _make_hardware_specs()
        state = create_initial_state(hw)
        state["throttle_demand"] = 1.0
        state["speed_kmh"] = 100.0
        state["gear"] = 4
        state["laps_total"] = 50
        state["lap"] = 1
        parts = get_defaults()
        physics = _make_physics_state()

        new_state, _ = run_parts_tick(parts, state, physics, hw, dt=1 / 30)
        assert new_state["fuel_remaining_kg"] < state["fuel_remaining_kg"]
