"""Sprint 11: ERS + brake temp wiring tests (T11.4)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulation import RaceSim
from engine.track_gen import generate_track, interpolate_track


def _make_cars(n=2):
    return [
        {
            "CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}",
            "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
            "strategy": lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"},
        }
        for i in range(n)
    ]


def _sim(laps=1, n_cars=2):
    track = interpolate_track(generate_track(seed=42), resolution=500)
    return RaceSim(_make_cars(n_cars), track, laps=laps, seed=42)


class TestERSWiring:
    def test_ers_state_initialized(self):
        sim = _sim()
        for s in sim.states:
            assert "ers" in s
            assert s["ers"]["energy"] == 4.0

    def test_ers_in_strategy_state(self):
        sim = _sim()
        from engine.replay import _compute_positions
        pos = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], pos)
        assert "ers_energy" in ss
        assert isinstance(ss["ers_energy"], float)

    def test_ers_depletes_during_race(self):
        sim = _sim(laps=1)
        sim.run()
        # At least one car should have used some ERS energy at some point
        # Check replay for ers_energy < 4.0
        replay = sim.export_replay()
        found_depletion = False
        for frame in replay["frames"][10:]:
            for car in frame:
                if car.get("ers_energy", 4.0) < 3.9:
                    found_depletion = True
                    break
            if found_depletion:
                break
        assert found_depletion, "ERS never depleted"


class TestBrakeTempWiring:
    def test_brake_state_initialized(self):
        sim = _sim()
        for s in sim.states:
            assert "brake_state" in s
            assert s["brake_state"]["temp"] == 20.0

    def test_brake_temp_in_strategy_state(self):
        sim = _sim()
        from engine.replay import _compute_positions
        pos = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], pos)
        assert "brake_temp" in ss
        assert isinstance(ss["brake_temp"], float)

    def test_brake_temp_rises(self):
        sim = _sim(laps=1)
        sim.run()
        replay = sim.export_replay()
        max_temp = max(
            car.get("brake_temp", 20.0)
            for frame in replay["frames"] for car in frame
        )
        assert max_temp > 20.0, f"Brakes never heated: max temp {max_temp}"


class TestReplayFields:
    def test_replay_has_ers_energy(self):
        sim = _sim()
        sim.run()
        replay = sim.export_replay()
        for car in replay["frames"][0]:
            assert "ers_energy" in car

    def test_replay_has_brake_temp(self):
        sim = _sim()
        sim.run()
        replay = sim.export_replay()
        for car in replay["frames"][0]:
            assert "brake_temp" in car
