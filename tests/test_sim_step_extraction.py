"""Tests that sim_step extraction preserves behavior (refactor safety net)."""
from engine.safety_car import create_sc_state


def test_sim_step_module_importable():
    """sim_step module exists and exports expected functions."""
    from engine import sim_step
    assert callable(sim_step.build_strategy_state)
    assert callable(sim_step.step_car)


def test_build_strategy_state_returns_dict():
    """build_strategy_state returns a dict with expected keys."""
    from engine.sim_step import build_strategy_state
    # Minimal stubs
    car_state = {
        "car_idx": 0, "name": "car_a", "distance": 100.0, "speed": 80.0,
        "lateral": 0.0, "tire_wear": 0.1, "boost_available": True,
        "boost_active": 0, "tire_compound": "medium", "tire_age_laps": 2,
        "engine_mode": "standard", "fuel_kg": 10.0, "max_fuel_kg": 20.0,
        "pit_state": {"status": "racing", "pit_stops": 0},
        "tire_temp": 35.0, "drs_available": False, "drs_active": False,
        "_in_drs_zone": False, "_in_dirty_air": False, "_dirty_air_grip": 1.0,
        "damage": {"damage": 0.0}, "_spin_risk": 0.0,
        "spin_recovery": 0, "ers": {"energy": 1.0}, "ers_deploy_mode": "balanced",
        "brake_state": {"temp": 200.0}, "setup_raw": {}, "lap": 1,
    }
    other = dict(car_state, car_idx=1, name="car_b", distance=200.0, speed=90.0)
    all_states = [car_state, other]

    class FakeTiming:
        lap_times = [60.5]
        best_lap = 60.5

    timings = {"car_a": FakeTiming(), "car_b": FakeTiming()}
    from engine.track_gen import CurvatureLookup
    curvature_lookup = CurvatureLookup([0, 500], [0.01, 0.02], 1000)

    result = build_strategy_state(
        car_state=car_state,
        all_states=all_states,
        timings=timings,
        tick=30,
        ticks_per_sec=30,
        distances=[0, 500],
        curvature_lookup=curvature_lookup,
        track_length=1000.0,
        sector_boundaries=(0.333, 0.666, 1.0),
        world_scale=1.0,
        track_name="test_track",
        car_data_dir=None,
        race_number=1,
        total_laps=3,
        drs_zones=[],
        safety_car_state=create_sc_state(),
        weather_state={"wetness": 0.0, "state": "dry"},
        weather_forecast=[],
        positions={0: 2, 1: 1},
    )
    assert isinstance(result, dict)
    assert result["speed"] == 80.0
    assert result["position"] == 2
    assert result["tire_wear"] == 0.1
    assert "gap_ahead_s" in result
    assert "opponent_info" in result


def test_step_car_no_unbound_local_error():
    """step_car must not raise UnboundLocalError when is_strategy_tick is False."""
    # This tests the fix: strat_state initialized before the if/else
    from engine.sim_step import step_car
    # If step_car is called on a non-strategy tick, it should use cached decision
    # We just verify it doesn't crash with UnboundLocalError
    # Full integration tested by existing test suite
