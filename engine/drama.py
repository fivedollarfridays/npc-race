"""Drama helpers: collision handling, spin risk, SC/weather updates."""
from .collision import check_collisions
from .damage import apply_damage
from .incident import compute_spin_risk, check_spin, create_spin_event
from .safety_car import (trigger_sc, update_sc, is_sc_active,
                          should_compress_gaps)
from .weather_model import update_weather, generate_forecast
from .tire_model import compute_grip_multiplier


def process_collisions(states, rng, safety_car, tick):
    """Apply collision events and decrement contact cooldowns."""
    for ev in check_collisions(states, rng):
        for s in states:
            if s["name"] in (ev["car_a"], ev["car_b"]):
                s["contact_cooldown"] = 60
                s["speed"] = max(0, s["speed"] - ev["speed_loss"])
                if ev["damage"] > 0:
                    s["damage"] = apply_damage(s["damage"], ev["damage"])
                    if s["damage"]["dnf"] and not s["finished"]:
                        s["finished"], s["finish_tick"] = True, tick
                        safety_car = trigger_sc(
                            safety_car, "collision", rng,
                            tick, s.get("lap", 0))
                if ev["spin"] and s["name"] == ev["car_b"]:
                    s["spin_recovery"] = 120
    for s in states:
        if s["contact_cooldown"] > 0:
            s["contact_cooldown"] -= 1
    return states, safety_car


def update_step_systems(states, safety_car, weather, rng, sc_last_lap,
                        weather_forecast):
    """Update SC, weather, gap compression, and propagate flags."""
    leader = max(states, key=lambda s: s["distance"])
    if leader["lap"] != sc_last_lap:
        sc_last_lap = leader["lap"]
        safety_car = update_sc(safety_car, leader["lap"])
        weather = update_weather(weather, rng)
        weather_forecast = generate_forecast(weather, 5, rng)
    if should_compress_gaps(safety_car):
        by_dist = sorted(states, key=lambda s: -s["distance"])
        for i in range(1, len(by_dist)):
            if by_dist[i]["finished"]:
                continue
            gap = by_dist[i - 1]["distance"] - by_dist[i]["distance"]
            if gap > 6.0:
                by_dist[i]["distance"] += (gap - 3.0) * 0.01
    for s in states:
        s["_safety_car"] = is_sc_active(safety_car)
        s["_track_wetness"] = weather.get("wetness", 0.0)
    return safety_car, weather, weather_forecast, sc_last_lap


def process_spin_risk(state, curv, safety_car, rng, tick):
    """Check spin risk and create spin event if triggered."""
    grip_avail = compute_grip_multiplier(
        state["tire_wear"], state.get("tire_compound", "medium"))
    grip_demand = curv * state["speed"] / 200.0
    spin_risk = compute_spin_risk(
        grip_avail, grip_demand, state.get("_dirty_air_grip", 1.0),
        state["tire_wear"], state.get("tire_age_laps", 0))
    state["_spin_risk"] = spin_risk
    if check_spin(spin_risk, rng):
        ev = create_spin_event(rng)
        state["spin_recovery"] = ev["recovery_ticks"]
        state["tire_wear"] = min(1.0, state["tire_wear"] + ev["tire_penalty"])
        state["speed"] = 20.0
        if ev.get("trigger_sc") and curv > 0.05:
            safety_car = trigger_sc(
                safety_car, "spin", rng, tick,
                state.get("lap", 0))
    return state, safety_car
