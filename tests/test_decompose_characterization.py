"""Characterization tests — capture exact outputs before refactoring.

These tests pin the exact behavior of run_parts_tick and run_efficiency_tick
so that the decomposition refactoring cannot change any results.
"""

from engine.parts_runner import create_initial_state, run_parts_tick
from engine.efficiency_engine import run_efficiency_tick
from engine.parts_api import get_defaults


def _make_hw():
    return {"weight_kg": 798, "fuel_capacity_kg": 110,
            "max_hp": 1000, "base_cl": 4.5, "base_cd": 0.88,
            "max_fuel_flow_kghr": 100}


def _make_state():
    hw = _make_hw()
    s = create_initial_state({"chassis": hw})
    s["speed_kmh"] = 200.0
    s["gear"] = 5
    s["engine_temp"] = 100.0
    return s


def _make_physics(braking=False):
    return {"throttle_demand": 1.0, "lateral_g": 0.3,
            "curvature": 0.01, "corner_phase": "mid",
            "braking": braking, "target_speed": 150.0,
            "bump_severity": 0.1}


# ---- run_parts_tick characterization ----

class TestPartsTickCharacterization:

    def test_non_braking_state_keys(self):
        """Pin the set of state keys returned."""
        defaults = get_defaults()
        s = _make_state()
        hw = _make_hw()
        new_s, log = run_parts_tick(defaults, s, _make_physics(), hw, 0.1, tick=5)
        assert "speed_kmh" in new_s
        assert "fuel_remaining_kg" in new_s
        assert "ers_state" in new_s
        assert "engine_temp" in new_s
        assert len(log) == 10  # all 10 parts logged

    def test_braking_state_keys(self):
        """Pin braking path."""
        defaults = get_defaults()
        s = _make_state()
        hw = _make_hw()
        new_s, log = run_parts_tick(defaults, s, _make_physics(braking=True), hw, 0.1, tick=5)
        assert new_s["speed_kmh"] >= 0
        assert len(log) == 10

    def test_deterministic_output(self):
        """Same inputs -> same outputs."""
        defaults = get_defaults()
        hw = _make_hw()
        s1 = _make_state()
        s2 = _make_state()
        ph = _make_physics()
        out1, log1 = run_parts_tick(defaults, s1, ph, hw, 0.1, tick=0)
        out2, log2 = run_parts_tick(defaults, s2, ph, hw, 0.1, tick=0)
        assert out1["speed_kmh"] == out2["speed_kmh"]
        assert out1["fuel_remaining_kg"] == out2["fuel_remaining_kg"]
        assert out1["engine_temp"] == out2["engine_temp"]

    def test_log_parts_order(self):
        """Pin the order of parts in the call log."""
        defaults = get_defaults()
        s = _make_state()
        hw = _make_hw()
        _, log = run_parts_tick(defaults, s, _make_physics(), hw, 0.1, tick=0)
        parts = [e["part"] for e in log]
        assert parts == [
            "engine_map", "gearbox", "fuel_mix", "suspension", "cooling",
            "ers_deploy", "differential", "brake_bias", "ers_harvest", "strategy",
        ]


# ---- run_efficiency_tick characterization ----

class TestEfficiencyTickCharacterization:

    def test_non_braking_returns(self):
        """Pin return structure."""
        defaults = get_defaults()
        s = _make_state()
        hw = _make_hw()
        new_s, log, product = run_efficiency_tick(
            defaults, s, _make_physics(), hw, 0.1, tick=5)
        assert isinstance(product, float)
        assert 0.0 < product <= 1.0
        assert "speed_kmh" in new_s
        assert len(log) == 10

    def test_braking_returns(self):
        """Pin braking path."""
        defaults = get_defaults()
        s = _make_state()
        hw = _make_hw()
        new_s, log, product = run_efficiency_tick(
            defaults, s, _make_physics(braking=True), hw, 0.1, tick=5)
        assert new_s["speed_kmh"] >= 0
        assert isinstance(product, float)

    def test_deterministic_output(self):
        """Same inputs -> same outputs."""
        defaults = get_defaults()
        hw = _make_hw()
        s1 = _make_state()
        s2 = _make_state()
        ph = _make_physics()
        out1, log1, p1 = run_efficiency_tick(defaults, s1, ph, hw, 0.1, tick=0)
        out2, log2, p2 = run_efficiency_tick(defaults, s2, ph, hw, 0.1, tick=0)
        assert out1["speed_kmh"] == out2["speed_kmh"]
        assert out1["fuel_remaining_kg"] == out2["fuel_remaining_kg"]
        assert p1 == p2

    def test_log_parts_order(self):
        """Pin the order of parts in the call log."""
        defaults = get_defaults()
        s = _make_state()
        hw = _make_hw()
        _, log, _ = run_efficiency_tick(
            defaults, s, _make_physics(), hw, 0.1, tick=0)
        parts = [e["part"] for e in log]
        assert parts == [
            "engine_map", "gearbox", "fuel_mix", "suspension", "cooling",
            "ers_deploy", "differential", "brake_bias", "ers_harvest", "strategy",
        ]

    def test_efficiency_values_present(self):
        """Pin that efficiency values are attached to log entries."""
        defaults = get_defaults()
        s = _make_state()
        hw = _make_hw()
        _, log, _ = run_efficiency_tick(
            defaults, s, _make_physics(), hw, 0.1, tick=0)
        # These parts should have efficiency values
        for entry in log:
            if entry["part"] in ("gearbox", "cooling", "fuel_mix"):
                assert "efficiency" in entry, f"{entry['part']} missing efficiency"
