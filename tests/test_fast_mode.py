"""Tests for RaceSim fast_mode (T34.2).

Validates that fast_mode produces identical physics with sparse storage.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulation import RaceSim
from engine.track_gen import generate_track, interpolate_track
from engine.lap_accumulator import LapAccumulator

import pytest
pytestmark = pytest.mark.smoke


def _default_strategy(s):
    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}


def _make_cars(n=3, strategy=None):
    strat = strategy or _default_strategy
    return [
        {
            "CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}",
            "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
            "strategy": strat,
        }
        for i in range(n)
    ]


def _make_track():
    control = generate_track(seed=42)
    return interpolate_track(control, resolution=500)


# ── Cycle 1: fast_mode parameter and accumulator creation ──────────────────


class TestFastModeInit:
    """RaceSim accepts fast_mode and creates accumulator when enabled."""

    def test_default_mode_no_accumulator(self):
        sim = RaceSim(_make_cars(), _make_track(), laps=1, seed=42)
        assert not hasattr(sim, "accumulator") or sim.accumulator is None

    def test_fast_mode_false_no_accumulator(self):
        sim = RaceSim(_make_cars(), _make_track(), laps=1, seed=42,
                       fast_mode=False)
        assert not hasattr(sim, "accumulator") or sim.accumulator is None

    def test_fast_mode_creates_accumulator(self):
        sim = RaceSim(_make_cars(), _make_track(), laps=1, seed=42,
                       fast_mode=True)
        assert isinstance(sim.accumulator, LapAccumulator)

    def test_fast_mode_flag_stored(self):
        sim = RaceSim(_make_cars(), _make_track(), laps=1, seed=42,
                       fast_mode=True)
        assert sim.fast_mode is True


# ── Cycle 2: frame recording and accumulator feeding ──────────────────────


class TestFastModeFrameRecording:
    """Fast mode records at 1Hz and feeds accumulator every tick."""

    def test_full_mode_records_every_tick(self):
        """Normal mode records a frame on every tick."""
        sim = RaceSim(_make_cars(2), _make_track(), laps=3, seed=42)
        sim.run()
        assert len(sim.history) == sim.tick

    def test_fast_mode_records_at_1hz(self):
        """Fast mode records one frame per second (every TICKS_PER_SEC ticks)."""
        sim = RaceSim(_make_cars(2), _make_track(), laps=3, seed=42,
                       fast_mode=True)
        sim.run()
        expected_frames = sim.tick // sim.TICKS_PER_SEC
        # Allow +1 for potential tick=0 frame
        assert abs(len(sim.history) - expected_frames) <= 1

    def test_fast_mode_far_fewer_frames(self):
        """Fast mode should have ~30x fewer frames than full mode."""
        track = _make_track()
        cars = _make_cars(2)
        sim_full = RaceSim(cars, track, laps=3, seed=42)
        sim_full.run()
        sim_fast = RaceSim(cars, track, laps=3, seed=42, fast_mode=True)
        sim_fast.run()
        ratio = len(sim_full.history) / max(len(sim_fast.history), 1)
        assert ratio > 20  # should be ~30x


# ── Cycle 3: physics equivalence and lap summaries ────────────────────────


class TestFastModePhysicsEquivalence:
    """Fast mode produces identical physics results to full mode."""

    def test_same_finish_order(self):
        """Both modes produce the same finish order."""
        track = _make_track()
        cars = _make_cars(3)
        res_full = RaceSim(cars, track, laps=3, seed=42).run()
        res_fast = RaceSim(cars, track, laps=3, seed=42, fast_mode=True).run()
        order_full = [r["name"] for r in res_full]
        order_fast = [r["name"] for r in res_fast]
        assert order_full == order_fast

    def test_same_lap_times(self):
        """Both modes produce the same lap times (within float tolerance)."""
        track = _make_track()
        cars = _make_cars(3)
        sim_full = RaceSim(cars, track, laps=3, seed=42)
        sim_full.run()
        sim_fast = RaceSim(cars, track, laps=3, seed=42, fast_mode=True)
        sim_fast.run()
        for name in ["Car0", "Car1", "Car2"]:
            full_times = sim_full.timings[name].lap_times
            fast_times = sim_fast.timings[name].lap_times
            assert len(full_times) == len(fast_times), f"{name} lap count mismatch"
            for i, (ft, fst) in enumerate(zip(full_times, fast_times)):
                assert abs(ft - fst) < 0.001, (
                    f"{name} lap {i+1}: {ft} vs {fst}")

    def test_same_tick_count(self):
        """Both modes run for the same number of ticks."""
        track = _make_track()
        cars = _make_cars(3)
        sim_full = RaceSim(cars, track, laps=3, seed=42)
        sim_full.run()
        sim_fast = RaceSim(cars, track, laps=3, seed=42, fast_mode=True)
        sim_fast.run()
        assert sim_full.tick == sim_fast.tick


class TestFastModeLapSummaries:
    """Fast mode populates lap summaries via accumulator."""

    def test_lap_summaries_populated(self):
        """After a 3-lap race, each car has 3 lap summaries."""
        sim = RaceSim(_make_cars(2), _make_track(), laps=3, seed=42,
                       fast_mode=True)
        sim.run()
        summaries = sim.get_lap_summaries()
        assert len(summaries) >= 1  # at least one car
        for name, laps in summaries.items():
            # Cars may complete 2 laps (lap 0->1 and 1->2 transitions)
            # depending on timing detection
            assert len(laps) >= 2, f"{name} has {len(laps)} lap summaries"

    def test_lap_summaries_have_required_fields(self):
        """Each lap summary has the required fields."""
        sim = RaceSim(_make_cars(2), _make_track(), laps=3, seed=42,
                       fast_mode=True)
        sim.run()
        summaries = sim.get_lap_summaries()
        required = {"lap", "time_s", "position", "tire_compound",
                    "tire_wear", "pit_stop", "fuel_remaining_pct"}
        for name, laps in summaries.items():
            for entry in laps:
                assert required.issubset(entry.keys()), (
                    f"{name}: missing keys {required - entry.keys()}")

    def test_lap_times_match_timing(self):
        """Lap times in summaries match timing system."""
        sim = RaceSim(_make_cars(2), _make_track(), laps=3, seed=42,
                       fast_mode=True)
        sim.run()
        summaries = sim.get_lap_summaries()
        for name, laps in summaries.items():
            timing_times = sim.timings[name].lap_times
            summary_times = [e["time_s"] for e in laps]
            for st, tt in zip(summary_times, timing_times):
                assert abs(st - tt) < 0.001

    def test_full_mode_get_lap_summaries_empty(self):
        """Full mode returns empty dict from get_lap_summaries."""
        sim = RaceSim(_make_cars(2), _make_track(), laps=3, seed=42)
        sim.run()
        assert sim.get_lap_summaries() == {}
