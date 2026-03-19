"""Tests for engine.drama — extracted step helpers."""
import random
from engine.drama import process_collisions, update_step_systems, process_spin_risk
from engine.damage import create_damage_state
from engine.safety_car import create_sc_state
from engine.weather_model import create_weather_state


def _make_state(idx, name, distance=100.0, speed=200.0, finished=False):
    return {
        "car_idx": idx, "name": name, "distance": distance,
        "speed": speed, "lap": 1, "finished": finished,
        "finish_tick": None, "contact_cooldown": 0,
        "damage": create_damage_state(), "spin_recovery": 0,
        "tire_wear": 0.3, "tire_compound": "medium",
        "tire_age_laps": 5, "lateral": 0.0,
        "_dirty_air_grip": 1.0, "_safety_car": False,
        "_track_wetness": 0.0,
    }


class TestProcessCollisions:
    """process_collisions applies collision events to states."""

    def test_returns_states_and_sc(self):
        rng = random.Random(42)
        states = [_make_state(0, "A"), _make_state(1, "B", distance=200.0)]
        sc = create_sc_state()
        new_states, new_sc = process_collisions(states, rng, sc, tick=10)
        assert isinstance(new_states, list)
        assert isinstance(new_sc, dict)

    def test_no_crash_when_cars_far_apart(self):
        rng = random.Random(42)
        states = [_make_state(0, "A", distance=0.0), _make_state(1, "B", distance=500.0)]
        sc = create_sc_state()
        new_states, new_sc = process_collisions(states, rng, sc, tick=10)
        assert new_states[0]["speed"] == 200.0
        assert new_states[1]["speed"] == 200.0

    def test_cooldown_decremented(self):
        rng = random.Random(42)
        states = [_make_state(0, "A"), _make_state(1, "B", distance=200.0)]
        states[0]["contact_cooldown"] = 5
        new_states, _ = process_collisions(states, rng, create_sc_state(), tick=10)
        assert new_states[0]["contact_cooldown"] == 4


class TestUpdateStepSystems:
    """update_step_systems handles SC, weather, gap compression."""

    def test_returns_four_values(self):
        rng = random.Random(42)
        states = [_make_state(0, "A")]
        sc = create_sc_state()
        weather = create_weather_state()
        result = update_step_systems(states, sc, weather, rng, sc_last_lap=-1,
                                     weather_forecast=[])
        assert len(result) == 4
        sc_out, weather_out, forecast, last_lap = result
        assert isinstance(sc_out, dict)
        assert isinstance(weather_out, dict)
        assert isinstance(forecast, list)

    def test_propagates_sc_flag_to_states(self):
        rng = random.Random(42)
        states = [_make_state(0, "A")]
        sc = create_sc_state()
        weather = create_weather_state()
        update_step_systems(states, sc, weather, rng, sc_last_lap=-1,
                            weather_forecast=[])
        assert "_safety_car" in states[0]
        assert "_track_wetness" in states[0]

    def test_leader_lap_triggers_update(self):
        rng = random.Random(42)
        states = [_make_state(0, "A")]
        states[0]["lap"] = 2
        sc = create_sc_state()
        weather = create_weather_state()
        sc_out, weather_out, forecast, last_lap = update_step_systems(
            states, sc, weather, rng, sc_last_lap=1, weather_forecast=[])
        assert last_lap == 2

    def test_no_lap_change_keeps_forecast(self):
        rng = random.Random(42)
        states = [_make_state(0, "A")]
        states[0]["lap"] = 2
        sc = create_sc_state()
        weather = create_weather_state()
        existing = [{"lap": 3, "state": "dry"}]
        _, _, forecast, _ = update_step_systems(
            states, sc, weather, rng, sc_last_lap=2, weather_forecast=existing)
        assert forecast == existing


class TestProcessSpinRisk:
    """process_spin_risk checks spin and mutates state if triggered."""

    def test_returns_state_and_sc(self):
        rng = random.Random(42)
        state = _make_state(0, "A", speed=50.0)
        state["tire_wear"] = 0.1
        sc = create_sc_state()
        new_state, new_sc = process_spin_risk(
            state, curv=0.01, safety_car=sc, rng=rng, tick=10)
        assert isinstance(new_state, dict)
        assert isinstance(new_sc, dict)

    def test_low_speed_low_curv_no_spin(self):
        rng = random.Random(42)
        state = _make_state(0, "A", speed=30.0)
        state["tire_wear"] = 0.05
        sc = create_sc_state()
        new_state, _ = process_spin_risk(
            state, curv=0.001, safety_car=sc, rng=rng, tick=10)
        assert new_state["spin_recovery"] == 0

    def test_spin_risk_stored_in_state(self):
        rng = random.Random(42)
        state = _make_state(0, "A", speed=200.0)
        state["tire_wear"] = 0.5
        sc = create_sc_state()
        new_state, _ = process_spin_risk(
            state, curv=0.1, safety_car=sc, rng=rng, tick=10)
        assert "_spin_risk" in new_state
