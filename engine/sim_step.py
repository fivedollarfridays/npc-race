"""Per-car step logic extracted from simulation.py for modularity."""
from .dirty_air import compute_dirty_air_factor
from .drama import process_spin_risk
from .ers_model import update_ers
from .brake_model import update_brake_temp
from .driver_model import compute_driver_inputs
from .fuel_model import compute_fuel_consumption
from .pit_lane import request_pit_stop, update_pit_state, complete_pit_stop
from .tire_model import compute_wear
from .tire_temperature import heat_generation, heat_dissipation, update_tire_temp
from .drs_system import is_in_drs_zone, update_drs_state
from .damage import repair_in_pit
from .safety_car import get_sc_modifiers, is_sc_active
from .weather_model import get_wetness_wear_mult
from .visibility import build_opponent_info, filter_nearby_cars
from .timing import update_timing
import os

VALID_ENGINE_MODES = {"push", "standard", "conserve"}


def _compute_gaps(car_state, all_states, world_scale):
    """Compute time gaps to car ahead and behind."""
    by_dist = sorted(all_states, key=lambda s: -s["distance"])
    mi = next(i for i, s in enumerate(by_dist) if s["car_idx"] == car_state["car_idx"])
    gap_a = gap_b = 0.0
    if mi > 0:
        spd = by_dist[mi - 1]["speed"] * (1 / 3.6) * world_scale
        gap_a = (by_dist[mi - 1]["distance"] - car_state["distance"]) / spd if spd > 0 else 0.0
    if mi < len(by_dist) - 1:
        spd = car_state["speed"] * (1 / 3.6) * world_scale
        gap_b = (car_state["distance"] - by_dist[mi + 1]["distance"]) / spd if spd > 0 else 0.0
    return gap_a, gap_b


def build_strategy_state(*, car_state, all_states, timings, tick,
                         ticks_per_sec, distances, curvature_lookup,
                         track_length, sector_boundaries, world_scale,
                         track_name, car_data_dir, race_number, total_laps,
                         drs_zones, safety_car_state, weather_state,
                         weather_forecast, positions):
    """Build state dict for car strategy functions (extracted from RaceSim)."""
    cs = car_state
    ps = cs.get("pit_state", {})
    nearby = filter_nearby_cars([
        {"name": o["name"], "distance_ahead": o["distance"] - cs["distance"],
         "speed": o["speed"], "lateral": o["lateral"],
         "tire_compound": o.get("tire_compound", "medium"),
         "tire_age_laps": o.get("tire_age_laps", 0)}
        for o in all_states if o["car_idx"] != cs["car_idx"]
        and abs(o["distance"] - cs["distance"]) < 100])
    gap_a, gap_b = _compute_gaps(cs, all_states, world_scale)
    df = os.path.join(car_data_dir, f"{cs['name']}.json") if car_data_dir else None
    ct = timings[cs["name"]]
    return {
        "speed": cs["speed"], "position": positions[cs["car_idx"]],
        "total_cars": len(all_states), "lap": cs["lap"], "total_laps": total_laps,
        "tire_wear": cs["tire_wear"], "boost_available": cs["boost_available"],
        "boost_active": cs["boost_active"] > 0, "nearby_cars": nearby,
        "curvature": curvature_lookup[cs["distance"]],
        "distance": cs["distance"], "track_length": track_length, "lateral": cs["lateral"],
        "fuel_remaining": cs["fuel_kg"], "fuel_pct": cs["fuel_kg"] / max(cs.get("max_fuel_kg", 1.0), 0.001),
        "tire_compound": cs.get("tire_compound", "medium"), "tire_age_laps": cs.get("tire_age_laps", 0),
        "engine_mode": cs.get("engine_mode", "standard"),
        "pit_status": ps.get("status", "racing"), "pit_stops": ps.get("pit_stops", 0),
        "gap_ahead_s": gap_a, "gap_behind_s": gap_b, "track_name": track_name,
        "data_file": df, "race_number": race_number,
        "tire_temp": cs["tire_temp"], "drs_available": cs["drs_available"],
        "drs_active": cs["drs_active"], "in_drs_zone": cs.get("_in_drs_zone", False),
        "current_setup": cs.get("setup_raw", {}),
        "in_dirty_air": cs.get("_in_dirty_air", False), "dirty_air_factor": cs.get("_dirty_air_grip", 1.0),
        "damage": cs["damage"]["damage"], "spin_risk": cs.get("_spin_risk", 0.0),
        "safety_car": is_sc_active(safety_car_state),
        "safety_car_laps": safety_car_state.get("laps_remaining", 0), "in_spin": cs["spin_recovery"] > 0,
        "elapsed_s": tick / ticks_per_sec,
        "last_lap_time": ct.lap_times[-1] if ct.lap_times else None, "best_lap_time": ct.best_lap,
        "ers_energy": cs["ers"]["energy"], "ers_deploy_mode": cs["ers_deploy_mode"],
        "brake_temp": cs["brake_state"]["temp"],
        "track_wetness": weather_state.get("wetness", 0.0),
        "weather_forecast": list(weather_forecast),
        "weather_state": weather_state.get("state", "dry"),
        "opponent_info": build_opponent_info(
            all_states, cs["car_idx"], positions, timings,
            ticks_per_sec, tick),
    }



def _apply_boost(state, wants_boost, ticks_per_sec):
    """Handle boost activation and countdown."""
    if wants_boost and state["boost_available"] and state["boost_active"] == 0:
        state["boost_active"] = ticks_per_sec * 3  # 3 seconds
        state["boost_available"] = False
    if state["boost_active"] > 0:
        state["boost_active"] -= 1


def _apply_tire_wear(state, tire_mode, curvature_lookup, safety_car_state,
                     weather_state):
    """Apply tire wear using compound model. tire_mode modulates throttle."""
    throttle_factor = {"conserve": 0.4, "balanced": 0.7, "push": 1.0}.get(tire_mode, 0.7)
    throttle_factor *= state.get("_dirty_air_wear", 1.0)
    throttle_factor *= get_sc_modifiers(safety_car_state)["tire_deg_mult"]
    throttle_factor *= get_wetness_wear_mult(
        weather_state.get("wetness", 0.0), state.get("tire_compound", "medium"))
    curv = curvature_lookup[state["distance"]]
    state["tire_wear"] = compute_wear(
        state["tire_wear"], state.get("tire_compound", "medium"), throttle_factor, curv)


def _apply_tire_temp_drs(state, throttle, decision, gap_ahead_s, dt,
                         curvature_lookup, track_length, drs_zones):
    """Update tire temperature and DRS."""
    curv = curvature_lookup[state["distance"]]
    heat = heat_generation(throttle, curv, state["lateral"], dt) * state["setup"].get("temp_rate_mult", 1.0)
    state["tire_temp"] = update_tire_temp(state["tire_temp"], heat,
                                          heat_dissipation(state["tire_temp"], state["speed"], dt))
    dp = (state["distance"] % track_length) / track_length if track_length > 0 else 0.0
    in_zone = is_in_drs_zone(dp, drs_zones)
    lap_changed = state["lap"] > state.get("_prev_lap", 0)
    state["_prev_lap"] = state["lap"]
    state["drs_available"], state["drs_active"] = update_drs_state(
        state["drs_available"], state["drs_active"],
        bool(decision.get("drs_request", False)), in_zone, gap_ahead_s, lap_changed)
    state["_in_drs_zone"] = in_zone


def _process_pit(state, decision):
    """Handle pit stop requests and completion."""
    pit_request = bool(decision.get("pit_request", False))
    tire_compound_request = decision.get("tire_compound_request", None)
    if pit_request:
        compound = tire_compound_request or state.get("tire_compound", "medium")
        state["pit_state"] = request_pit_stop(state["pit_state"], compound)
    state["pit_state"], pit_completed = update_pit_state(state["pit_state"])
    if pit_completed:
        state["pit_state"], new_compound = complete_pit_stop(state["pit_state"])
        state["tire_compound"] = new_compound
        state["tire_wear"] = 0.0
        state["tire_age_laps"] = 0
        if state["damage"]["damage"] > 0.05:
            state["damage"], extra = repair_in_pit(state["damage"])
            state["spin_recovery"] = max(state["spin_recovery"], extra)


def _compute_dirty_air(state, gap_ahead_s, curvature):
    """Compute and store dirty air grip/wear penalties."""
    da_grip, da_wear = compute_dirty_air_factor(gap_ahead_s, curvature)
    state["_in_dirty_air"] = da_grip < 1.0
    state["_dirty_air_grip"] = da_grip
    state["_dirty_air_wear"] = da_wear


def _update_post_physics(state, curvature, engine_mode, throttle, dt,
                         safety_car_state, fuel_base_rate):
    """Update ERS, brake temp, and fuel after physics step."""
    braking_force = curvature * state["speed"] / 100.0
    state["ers"] = update_ers(state["ers"], state["ers_deploy_mode"], braking_force, dt)
    state["brake_state"] = update_brake_temp(
        state["brake_state"], braking_force, state["speed"], dt)
    if state["fuel_kg"] > 0:
        consumed = compute_fuel_consumption(throttle, engine_mode, fuel_base_rate, dt)
        consumed *= get_sc_modifiers(safety_car_state)["fuel_mult"]
        state["fuel_kg"] = max(0.0, state["fuel_kg"] - consumed)


def _update_timing(state, strat_state, is_strategy_tick, timings, track_length,
                   tick, ticks_per_sec, sector_boundaries, gap_ahead_s):
    """Update timing, gap tracking, and sector info."""
    dp = (state["distance"] % track_length) / track_length if track_length > 0 else 0.0
    tr = update_timing(timings, state["name"], dp, state["lap"],
                       tick, ticks_per_sec, sector_boundaries)
    state["_timing"] = tr
    state["_gap_ahead_s"] = gap_ahead_s
    state["_gap_behind_s"] = (strat_state["gap_behind_s"] if is_strategy_tick
                              else state.get("_gap_behind_s", 0.0))
    ct = timings[state["name"]]
    state["_last_lap_time"] = ct.lap_times[-1] if ct.lap_times else None
    state["_best_lap_s"] = ct.best_lap
    state["_last_sector_time"] = tr["sector_time"] if tr.get("sector_completed") else None
    state["_last_sector_idx"] = (tr.get("current_sector", 0) - 1
                                 if tr.get("sector_completed") else None)


def _resolve_decision(state, car, sim):
    """Get strategy decision, driver inputs, and gap; return parsed result."""
    positions = sim._current_positions
    strat_state = None
    is_strategy_tick = (sim.tick % sim.TICKS_PER_SEC == 0)
    if is_strategy_tick:
        strat_state = build_strategy_state(
            car_state=state, all_states=sim.states, timings=sim.timings,
            tick=sim.tick, ticks_per_sec=sim.TICKS_PER_SEC,
            distances=sim.distances, curvature_lookup=sim.curvature_lookup,
            track_length=sim.track_length,
            sector_boundaries=sim.sector_boundaries,
            world_scale=sim.world_scale, track_name=sim.track_name,
            car_data_dir=sim.car_data_dir, race_number=sim.race_number,
            total_laps=sim.laps, drs_zones=sim.drs_zones,
            safety_car_state=sim.safety_car, weather_state=sim.weather,
            weather_forecast=sim._weather_forecast, positions=positions)
        try:
            decision = car["strategy"](strat_state)
            if not isinstance(decision, dict):
                decision = {}
        except Exception:
            decision = {}
        state["_cached_decision"] = decision
        gap_ahead_s = strat_state["gap_ahead_s"]
    else:
        decision = state["_cached_decision"]
        gap_ahead_s = sim._compute_gap_ahead_s(state)

    driver = sim.drivers.get(state["name"])
    if driver:
        driver_inputs = compute_driver_inputs(
            driver, state, state["tire_wear"],
            sim.weather.get("wetness", 0.0), state["damage"]["damage"])
    else:
        driver_inputs = {"throttle": 1.0, "lateral_target": 0.0}

    throttle = max(0.0, min(1.0, decision.get("throttle", driver_inputs["throttle"])))
    lateral_target = float(decision.get("lateral_target", driver_inputs["lateral_target"]))
    engine_mode = decision.get("engine_mode", "standard")
    if engine_mode not in VALID_ENGINE_MODES:
        engine_mode = "standard"
    state["engine_mode"] = engine_mode
    ers_mode = decision.get("ers_deploy_mode", "balanced")
    if ers_mode not in ("attack", "balanced", "harvest"):
        ers_mode = "balanced"
    state["ers_deploy_mode"] = ers_mode
    return decision, throttle, lateral_target, engine_mode, gap_ahead_s, strat_state, is_strategy_tick


def step_car(state, car, sim):
    """Advance a single car by one tick (extracted from RaceSim._step_car)."""
    dt = 1.0 / sim.TICKS_PER_SEC
    spatial_index = sim._current_spatial_index

    decision, throttle, lateral_target, engine_mode, gap_ahead_s, strat_state, is_strategy_tick = (
        _resolve_decision(state, car, sim))

    # Spin recovery — skip most physics
    if state["spin_recovery"] > 0:
        state["spin_recovery"] -= 1
        state["speed"] = min(state["speed"], 20.0)
        sim._update_distance(state, dt)
        return

    _process_pit(state, decision)

    curv = sim.curvature_lookup[state["distance"]]
    _compute_dirty_air(state, gap_ahead_s, curv)

    wants_boost = bool(decision.get("boost", False))
    tire_mode = decision.get("tire_mode", "balanced")
    _apply_boost(state, wants_boost, sim.TICKS_PER_SEC)
    _apply_tire_wear(state, tire_mode, sim.curvature_lookup, sim.safety_car,
                     sim.weather)
    _apply_tire_temp_drs(state, throttle, decision, gap_ahead_s, dt,
                         sim.curvature_lookup, sim.track_length, sim.drs_zones)
    sim._apply_physics(state, throttle, dt)
    sim._apply_drafting(state, dt, spatial_index)
    sim._apply_lateral(state, lateral_target, dt, spatial_index)

    _update_post_physics(state, curv, engine_mode, throttle, dt,
                         sim.safety_car, state["fuel_base_rate"])
    sim._update_distance(state, dt)
    state, sim.safety_car = process_spin_risk(
        state, curv, sim.safety_car, sim.rng, sim.tick)

    _update_timing(state, strat_state, is_strategy_tick, sim.timings,
                   sim.track_length, sim.tick, sim.TICKS_PER_SEC,
                   sim.sector_boundaries, gap_ahead_s)
