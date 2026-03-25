"""Tests for PartsRaceSim compatibility with RaceSim interface (T42.1)."""

import pytest

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from tracks import get_track
from engine.track_gen import interpolate_track

CARS_DIR = "cars"


def _make_sim(n_cars=2, **kwargs):
    """Build a PartsRaceSim with sensible defaults, merging kwargs.

    Uses only *n_cars* cars to keep tests fast.
    """
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)[:n_cars]
    defaults = dict(
        laps=1, seed=42, track_name="monza",
        real_length_m=td.get("real_length_m"),
    )
    defaults.update(kwargs)
    return PartsRaceSim(cars, pts, **defaults)


class TestConstructorParams:
    """Cycle 1: constructor accepts all new params without crashing."""

    def test_constructor_accepts_all_params(self):
        sim = _make_sim(
            fast_mode=True, drs_zones=[], car_data_dir=None, race_number=1,
        )
        assert sim is not None

    def test_stores_car_data_dir(self):
        sim = _make_sim(car_data_dir="/tmp/cars")
        assert sim.car_data_dir == "/tmp/cars"

    def test_stores_race_number(self):
        sim = _make_sim(race_number=5)
        assert sim.race_number == 5

    def test_stores_drs_zones(self):
        zones = [{"start": 100, "end": 300}]
        sim = _make_sim(drs_zones=zones)
        assert sim.drs_zones == zones

    def test_drs_zones_defaults_none(self):
        sim = _make_sim()
        assert sim.drs_zones is None


class TestTimingsAndProperties:
    """Cycle 2: timings dict and states property compatibility."""

    def test_has_timings_after_init(self):
        sim = _make_sim()
        assert hasattr(sim, "timings")
        assert isinstance(sim.timings, dict)

    def test_timings_has_all_car_names(self):
        sim = _make_sim()
        car_names = {s["name"] for s in sim.car_states}
        assert set(sim.timings.keys()) == car_names

    def test_has_states_property(self):
        """RaceSim uses sim.states; PartsRaceSim should expose it too."""
        sim = _make_sim()
        assert hasattr(sim, "states")
        assert len(sim.states) == len(sim.car_states)

    def test_has_tick_after_step(self):
        sim = _make_sim()
        assert sim.tick == 0
        sim.step()
        assert sim.tick == 1

    @pytest.mark.timeout(60)
    def test_timings_after_run(self):
        sim = _make_sim(n_cars=2)
        sim.run(max_ticks=6000)
        # At least one car should have lap times recorded
        any_laps = any(
            ct.lap_times for ct in sim.timings.values()
        )
        assert any_laps, "Expected at least one car to have lap times"


class TestFastMode:
    """Cycle 3: fast_mode records fewer frames and integrates LapAccumulator."""

    @pytest.mark.timeout(60)
    def test_fast_mode_fewer_frames(self):
        """fast_mode=True records ~30x fewer frames than normal mode."""
        ticks = 900  # 30 seconds of simulation
        sim_normal = _make_sim(fast_mode=False, n_cars=2)
        for _ in range(ticks):
            sim_normal.step()
        sim_fast = _make_sim(fast_mode=True, n_cars=2)
        for _ in range(ticks):
            sim_fast.step()
        # fast_mode should have roughly 30x fewer frames
        ratio = len(sim_normal.history) / max(len(sim_fast.history), 1)
        assert ratio > 10, f"Expected >10x fewer frames, got {ratio:.1f}x"

    def test_fast_mode_accumulator_exists(self):
        sim = _make_sim(fast_mode=True)
        assert sim.accumulator is not None

    def test_normal_mode_no_accumulator(self):
        sim = _make_sim(fast_mode=False)
        assert sim.accumulator is None

    @pytest.mark.timeout(60)
    def test_get_lap_summaries_fast_mode(self):
        """get_lap_summaries returns per-car data after fast_mode run."""
        sim = _make_sim(fast_mode=True, n_cars=2)
        sim.run(max_ticks=6000)
        summaries = sim.get_lap_summaries()
        assert isinstance(summaries, dict)
        # At least one car should have completed a lap
        any_laps = any(len(laps) > 0 for laps in summaries.values())
        assert any_laps, "Expected at least one car to have lap summaries"

    def test_get_lap_summaries_normal_mode_empty(self):
        """get_lap_summaries returns empty dict when not in fast_mode."""
        sim = _make_sim(fast_mode=False)
        assert sim.get_lap_summaries() == {}
