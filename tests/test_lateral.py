"""Tests for lateral movement system (T3.4)."""

from engine.simulation import RaceSim


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_car(name="TestCar", strategy=None):
    """Create a minimal car dict for testing."""
    if strategy is None:
        def strategy(state):
            return {"throttle": 1.0}
    return {
        "CAR_NAME": name,
        "CAR_COLOR": "#ff0000",
        "POWER": 10,
        "GRIP": 10,
        "WEIGHT": 10,
        "AERO": 10,
        "BRAKES": 10,
        "strategy": strategy,
    }


def _make_sim(cars=None, laps=1, seed=42):
    """Create a RaceSim with minimal track."""
    if cars is None:
        cars = [_make_car()]
    # Simple square track
    track = [(100, 100), (700, 100), (700, 600), (100, 600)]
    return RaceSim(cars, track, laps=laps, seed=seed)


# ---------------------------------------------------------------------------
# Test: lateral_target=1.0 moves car toward 1.0
# ---------------------------------------------------------------------------

class TestLateralMovesTowardTarget:
    def test_positive_target_increases_lateral(self):
        """Car with lateral_target=1.0 should move lateral toward 1.0."""
        def strat(state):
            return {"throttle": 1.0, "lateral_target": 1.0}

        sim = _make_sim([_make_car(strategy=strat)])
        # Run several ticks
        for _ in range(60):
            sim.step()
        assert sim.states[0]["lateral"] > 0.0

    def test_negative_target_decreases_lateral(self):
        """Car with lateral_target=-1.0 should move lateral toward -1.0."""
        def strat(state):
            return {"throttle": 1.0, "lateral_target": -1.0}

        sim = _make_sim([_make_car(strategy=strat)])
        for _ in range(60):
            sim.step()
        assert sim.states[0]["lateral"] < 0.0

    def test_reaches_near_target_over_time(self):
        """After many ticks, lateral should be close to target."""
        def strat(state):
            return {"throttle": 1.0, "lateral_target": 1.0}

        sim = _make_sim([_make_car(strategy=strat)])
        for _ in range(300):
            sim.step()
        assert sim.states[0]["lateral"] > 0.5


# ---------------------------------------------------------------------------
# Test: default lateral_target=0.0 keeps car near center
# ---------------------------------------------------------------------------

class TestDefaultLateralTarget:
    def test_no_lateral_target_stays_bounded(self):
        """Strategy without lateral_target should keep car within track bounds."""
        def strat(state):
            return {"throttle": 1.0}

        sim = _make_sim([_make_car(strategy=strat)])
        for _ in range(60):
            sim.step()
        assert abs(sim.states[0]["lateral"]) <= 1.0


# ---------------------------------------------------------------------------
# Test: high-speed car changes lateral slower
# ---------------------------------------------------------------------------

class TestSpeedReducesAgility:
    def test_high_speed_slower_lateral_change(self):
        """A fast car should change lateral position slower than a slow one."""
        lateral_at_low_speed = None
        lateral_at_high_speed = None

        # Low speed car (low throttle)
        def strat_slow(state):
            return {"throttle": 0.1, "lateral_target": 1.0}

        sim_slow = _make_sim([_make_car(strategy=strat_slow)])
        for _ in range(60):
            sim_slow.step()
        lateral_at_low_speed = sim_slow.states[0]["lateral"]

        # High speed car (full throttle)
        def strat_fast(state):
            return {"throttle": 1.0, "lateral_target": 1.0}

        sim_fast = _make_sim([_make_car(strategy=strat_fast)])
        for _ in range(60):
            sim_fast.step()
        lateral_at_high_speed = sim_fast.states[0]["lateral"]

        # Slow car should have moved more laterally
        assert lateral_at_low_speed > lateral_at_high_speed


# ---------------------------------------------------------------------------
# Test: lateral is clamped to [-1, 1]
# ---------------------------------------------------------------------------

class TestLateralClamping:
    def test_lateral_never_exceeds_one(self):
        """Lateral should never go above 1.0."""
        def strat(state):
            return {"throttle": 1.0, "lateral_target": 5.0}

        sim = _make_sim([_make_car(strategy=strat)])
        for _ in range(300):
            sim.step()
        assert sim.states[0]["lateral"] <= 1.0

    def test_lateral_never_below_minus_one(self):
        """Lateral should never go below -1.0."""
        def strat(state):
            return {"throttle": 1.0, "lateral_target": -5.0}

        sim = _make_sim([_make_car(strategy=strat)])
        for _ in range(300):
            sim.step()
        assert sim.states[0]["lateral"] >= -1.0


# ---------------------------------------------------------------------------
# Test: proximity resistance pushes close cars apart
# ---------------------------------------------------------------------------

class TestProximityResistance:
    def test_close_cars_push_apart(self):
        """Two cars at same distance and lateral should be pushed apart."""
        def strat_center(state):
            return {"throttle": 0.5, "lateral_target": 0.0}

        car1 = _make_car(name="Car1", strategy=strat_center)
        car2 = _make_car(name="Car2", strategy=strat_center)

        sim = _make_sim([car1, car2])
        # Set both cars to same distance and lateral
        sim.states[0]["distance"] = 100.0
        sim.states[1]["distance"] = 100.0
        sim.states[0]["lateral"] = 0.0
        sim.states[1]["lateral"] = 0.0

        for _ in range(60):
            sim.step()

        # They should have different lateral positions due to push
        lat_diff = abs(sim.states[0]["lateral"] - sim.states[1]["lateral"])
        assert lat_diff > 0.01


# ---------------------------------------------------------------------------
# Test: backward compat -- old strategy without lateral_target
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_old_strategy_no_lateral_target(self):
        """Strategy returning only throttle should work (lateral_target defaults to 0.0)."""
        def old_strat(state):
            return {"throttle": 0.8}

        sim = _make_sim([_make_car(strategy=old_strat)])
        # Should not raise
        for _ in range(30):
            sim.step()
        # Lateral stays within track bounds (driver model may use racing line)
        assert abs(sim.states[0]["lateral"]) <= 1.0

    def test_empty_strategy_dict(self):
        """Empty dict strategy should not crash."""
        def empty_strat(state):
            return {}

        sim = _make_sim([_make_car(strategy=empty_strat)])
        for _ in range(30):
            sim.step()
        assert abs(sim.states[0]["lateral"]) <= 1.0
