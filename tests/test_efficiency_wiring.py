"""Tests for efficiency engine wiring into parts simulation."""

import pytest

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from tracks import get_track
from engine.track_gen import interpolate_track

CARS_DIR = "cars"


def _make_sim(laps=1):
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)
    return PartsRaceSim(cars, pts, laps=laps, seed=42, track_name="monza",
                        real_length_m=td.get("real_length_m"))


class TestEfficiencyWiring:
    def test_prev_states_initialized(self):
        """prev_states list should exist with None entries at init."""
        sim = _make_sim()
        assert hasattr(sim, "prev_states")
        assert len(sim.prev_states) == len(sim.cars)
        assert all(ps is None for ps in sim.prev_states)

    def test_efficiency_product_on_state_after_step(self):
        """After one step, each non-finished car state has efficiency_product."""
        sim = _make_sim()
        sim.step()
        for state in sim.car_states:
            assert "efficiency_product" in state
            assert 0 < state["efficiency_product"] <= 1.0

    def test_prev_states_populated_after_step(self):
        """After one step, prev_states should be dicts (not None)."""
        sim = _make_sim()
        sim.step()
        for ps in sim.prev_states:
            assert ps is not None
            assert isinstance(ps, dict)

    def test_position_and_gap_in_initial_state(self):
        """Car states should have position and gap_ahead at init."""
        sim = _make_sim()
        for state in sim.car_states:
            assert "position" in state
            assert "gap_ahead" in state

    def test_grip_factor_on_state(self):
        """grip_factor should be computed and stored on car state."""
        sim = _make_sim()
        for _ in range(10):
            sim.step()
        for state in sim.car_states:
            assert "grip_factor" in state, "grip_factor missing from car state"
            assert 0.3 < state["grip_factor"] < 2.0, \
                f"grip_factor out of range: {state['grip_factor']:.3f}"

    def test_race_completes_with_efficiency_engine(self):
        """Full race should still complete (cars finish)."""
        sim = _make_sim(laps=1)
        sim.run(max_ticks=6000)
        finished = [s for s in sim.car_states if s["finished"]]
        assert len(finished) >= 3
