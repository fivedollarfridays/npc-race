"""Sprint 12: Visibility wiring tests (T12.2)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulation import RaceSim
from engine.replay import _compute_positions
from engine.track_gen import generate_track, interpolate_track
from engine.visibility import PRIVATE_FIELDS


def _sim():
    track = interpolate_track(generate_track(seed=42), resolution=500)
    cars = [
        {"CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}", "POWER": 20,
         "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
         "strategy": lambda s: {"throttle": 1.0}}
        for i in range(3)
    ]
    return RaceSim(cars, track, laps=1, seed=42)


class TestStrategyStateAsymmetry:
    def test_has_opponent_info(self):
        sim = _sim()
        pos = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], pos)
        assert "opponent_info" in ss
        assert isinstance(ss["opponent_info"], list)
        assert len(ss["opponent_info"]) == 2  # 3 cars minus self

    def test_opponent_info_no_private_data(self):
        sim = _sim()
        pos = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], pos)
        for opp in ss["opponent_info"]:
            for field in PRIVATE_FIELDS:
                assert field not in opp, f"Private field leaked: {field}"

    def test_opponent_info_has_observable(self):
        sim = _sim()
        pos = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], pos)
        for opp in ss["opponent_info"]:
            assert "name" in opp
            assert "position" in opp
            assert "speed" in opp
            assert "tire_compound" in opp

    def test_nearby_cars_has_compound(self):
        sim = _sim()
        # Move cars close together so nearby_cars is populated
        for s in sim.states:
            s["distance"] = 100.0
        pos = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], pos)
        if ss["nearby_cars"]:
            car = ss["nearby_cars"][0]
            assert "tire_compound" in car
            assert "tire_age_laps" in car

    def test_own_car_has_full_data(self):
        sim = _sim()
        pos = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], pos)
        assert "tire_wear" in ss
        assert "fuel_remaining" in ss
        assert "damage" in ss
        assert "ers_energy" in ss
        assert "brake_temp" in ss
