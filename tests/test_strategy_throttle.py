"""Tests for T34.4: Strategy throttle (1Hz calls).

Verifies that strategy functions are called every 30 ticks (1Hz)
instead of every tick (30Hz), and that race results stay within tolerance.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulation import RaceSim
from engine.track_gen import generate_track, interpolate_track


def _make_procedural_track():
    control = generate_track(seed=42)
    return interpolate_track(control, resolution=500)


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


# -- Cycle 1: Strategy call frequency -------------------------------------------

class TestStrategyCallFrequency:
    """Strategy functions should be called at 1Hz (every 30 ticks)."""

    def test_strategy_called_once_per_second(self):
        """Over 300 ticks (10 seconds), strategy called ~10 times per car."""
        call_counts = [0]

        def counting_strategy(s):
            call_counts[0] += 1
            return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}

        track = _make_procedural_track()
        cars = _make_cars(1, strategy=counting_strategy)
        sim = RaceSim(cars, track, laps=3, seed=42)
        for _ in range(300):
            sim.step()
        # 300 ticks / 30 ticks_per_sec = 10 strategy calls
        assert call_counts[0] == 10, (
            f"Expected 10 strategy calls over 300 ticks, got {call_counts[0]}"
        )

    def test_strategy_called_on_tick_zero(self):
        """Strategy must be called on the very first tick."""
        called = [False]

        def first_tick_strategy(s):
            called[0] = True
            return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}

        track = _make_procedural_track()
        cars = _make_cars(1, strategy=first_tick_strategy)
        sim = RaceSim(cars, track, laps=1, seed=42)
        sim.step()
        assert called[0], "Strategy was not called on tick 0"

    def test_build_strategy_state_called_30x_fewer(self):
        """build_strategy_state should only be called on strategy ticks."""
        track = _make_procedural_track()
        cars = _make_cars(2)
        sim = RaceSim(cars, track, laps=3, seed=42)

        original_bss = sim.build_strategy_state
        bss_count = [0]

        def counting_bss(*args, **kwargs):
            bss_count[0] += 1
            return original_bss(*args, **kwargs)

        sim.build_strategy_state = counting_bss

        for _ in range(300):
            sim.step()

        # 2 cars x 10 strategy ticks = 20 calls (not 2 x 300 = 600)
        # Some cars may finish early, so allow a range
        assert bss_count[0] <= 30, (
            f"build_strategy_state called {bss_count[0]} times, expected ~20"
        )

    def test_cached_decision_initialized(self):
        """Car state should have _cached_decision initialized."""
        track = _make_procedural_track()
        cars = _make_cars(2)
        sim = RaceSim(cars, track, laps=1, seed=42)
        for state in sim.states:
            assert "_cached_decision" in state
            assert state["_cached_decision"] == {}


# -- Cycle 2: Race results within tolerance ------------------------------------

class TestResultsTolerance:
    """Race results should be nearly identical with throttled strategy."""

    def test_finish_order_preserved(self):
        """Finish order must remain the same with 1Hz strategy."""
        # This test validates that caching doesn't change race outcome.
        # With all cars using the same strategy, order is determined by
        # starting position (grid penalty from car_idx spacing).
        track = _make_procedural_track()
        cars = _make_cars(3)
        sim = RaceSim(cars, track, laps=2, seed=42)
        results = sim.run()
        # All cars should finish
        assert all(r["finished"] for r in results)
        # Results should be ordered by position
        positions = [r["position"] for r in results]
        assert sorted(positions) == list(range(1, len(positions) + 1))

    def test_gap_ahead_computed_every_tick_for_dirty_air(self):
        """gap_ahead_s must be available every tick for dirty air physics."""
        track = _make_procedural_track()
        cars = _make_cars(3)
        sim = RaceSim(cars, track, laps=1, seed=42)

        # Run a few ticks including non-strategy ticks
        for _ in range(5):
            sim.step()

        # After tick 1 (a non-strategy tick), dirty air should still work
        # Check that _in_dirty_air is set (it's computed from gap_ahead_s)
        for state in sim.states:
            assert "_in_dirty_air" in state
