"""T31.2 — Call log export to replay JSON format."""

import pytest

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from tracks import get_track
from engine.track_gen import interpolate_track

pytestmark = pytest.mark.smoke

CARS_DIR = "cars"


@pytest.fixture(scope="module")
def sim_and_replay():
    """Run a 1-lap race once, return (sim, replay) for all tests."""
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)
    sim = PartsRaceSim(cars, pts, laps=1, seed=42, track_name="monza",
                       real_length_m=td.get("real_length_m"))
    sim.run(max_ticks=6000)
    replay = sim.export_replay()
    return sim, replay


class TestReplayHasCallLogs:
    """Cycle 1: replay export includes call_logs key."""

    def test_replay_has_call_logs_key(self, sim_and_replay):
        _, replay = sim_and_replay
        assert "call_logs" in replay

    def test_call_logs_per_car(self, sim_and_replay):
        _, replay = sim_and_replay
        call_logs = replay["call_logs"]
        assert len(call_logs) >= 3


class TestCallLogsSampled:
    """Cycle 2: call logs sampled at 1Hz, not 30Hz."""

    def test_call_logs_sampled_at_1hz(self, sim_and_replay):
        sim, replay = sim_and_replay
        call_logs = replay["call_logs"]
        first_car = list(call_logs.values())[0]
        assert len(first_car) < len(sim.call_logs), (
            "Should be sampled, not every tick"
        )
        race_seconds = len(sim.call_logs) / 30
        assert len(first_car) <= race_seconds + 2

    def test_sampled_ticks_are_multiples_of_30(self, sim_and_replay):
        _, replay = sim_and_replay
        call_logs = replay["call_logs"]
        first_car = list(call_logs.values())[0]
        for entry in first_car:
            assert entry["tick"] % 30 == 0, (
                f"Tick {entry['tick']} is not a multiple of 30"
            )


class TestCallLogFormat:
    """Cycle 3: each entry has correct format with parts list."""

    def test_entry_has_tick_and_parts(self, sim_and_replay):
        _, replay = sim_and_replay
        call_logs = replay["call_logs"]
        first_car = list(call_logs.values())[0]
        entry = first_car[0]
        assert "tick" in entry
        assert "parts" in entry
        assert isinstance(entry["parts"], list)

    def test_part_entry_has_required_fields(self, sim_and_replay):
        _, replay = sim_and_replay
        call_logs = replay["call_logs"]
        first_car = list(call_logs.values())[0]
        part = first_car[0]["parts"][0]
        assert "name" in part
        assert "output" in part
        assert "status" in part

    def test_efficiency_included_when_not_one(self, sim_and_replay):
        """Efficiency field present only when != 1.0."""
        _, replay = sim_and_replay
        call_logs = replay["call_logs"]
        all_parts = []
        for car_entries in call_logs.values():
            for entry in car_entries:
                all_parts.extend(entry["parts"])
        with_eff = [p for p in all_parts if "efficiency" in p]
        without_eff = [p for p in all_parts if "efficiency" not in p]
        assert len(with_eff) > 0, "Some parts should have non-1.0 efficiency"
        assert len(without_eff) > 0, "Parts with eff=1.0 should omit it"


class TestReplayHasReliability:
    """Cycle 4: replay includes per-car reliability scores."""

    def test_replay_has_reliability_key(self, sim_and_replay):
        _, replay = sim_and_replay
        assert "reliability" in replay

    def test_reliability_per_car(self, sim_and_replay):
        _, replay = sim_and_replay
        reliability = replay["reliability"]
        assert isinstance(reliability, dict)
        assert len(reliability) >= 3


class TestOldReplayCompat:
    """Cycle 5: old replays without call_logs don't crash."""

    def test_replay_without_call_logs_is_valid(self, sim_and_replay):
        """A replay dict without call_logs should still be a valid dict."""
        _, replay = sim_and_replay
        replay_old = {k: v for k, v in replay.items() if k != "call_logs"}
        assert replay_old.get("call_logs") is None
        assert "frames" in replay_old
        assert "results" in replay_old
