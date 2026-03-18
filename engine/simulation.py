"""Race simulation: tire compounds, fuel, pit stops, engine modes, world-scale."""

import os
import random

from . import tire_model
from .track_gen import compute_track_data, compute_track_headings, get_curvature_at
from .replay import record_frame, get_results, export_replay, _compute_positions
from .tire_model import compute_wear, compute_grip_multiplier
from .fuel_model import (compute_starting_fuel, compute_fuel_consumption,
                         compute_weight_from_fuel, get_engine_mode)
from .pit_lane import (create_pit_state, request_pit_stop, update_pit_state,
                       is_in_pit, get_speed_limit, complete_pit_stop)
from .tire_temperature import (heat_generation, heat_dissipation,
                               update_tire_temp, tire_temp_grip_factor)
from .drs_system import is_in_drs_zone, drs_speed_multiplier, update_drs_state
from .physics import (compute_target_speed, compute_draft_bonus,
                      update_speed, compute_lateral_push, apply_drag,
                      MAX_SPEED, compute_aero_grip)
from .dirty_air import compute_dirty_air_factor
from .timing import create_timing, update_timing

VALID_ENGINE_MODES = {"push", "standard", "conserve"}


class RaceSim:
    TICKS_PER_SEC = 30
    TRACK_WIDTH = 50

    def __init__(self, cars, track_points, laps=3, seed=42, track_name=None,
                 real_length_m=None, car_data_dir=None, race_number=1,
                 drs_zones=None):
        self.cars, self.track, self.laps = cars, track_points, laps
        self.rng, self.track_name = random.Random(seed), track_name
        self.car_data_dir = car_data_dir
        self.race_number = race_number
        self.drs_zones = drs_zones or []
        self.distances, self.curvatures, self.track_length = compute_track_data(
            track_points)
        self.headings = compute_track_headings(track_points)
        self.n_points = len(track_points)
        if real_length_m and real_length_m > 0:
            self.world_scale = self.track_length / real_length_m
        else:
            self.world_scale = self.track_length / 5000.0  # fallback
        rlm = real_length_m if real_length_m and real_length_m > 0 else 5000.0
        start_fuel = compute_starting_fuel(laps, rlm)
        self.states = []
        for i, car in enumerate(cars):
            self.states.append({
                "car_idx": i, "name": car["CAR_NAME"], "color": car["CAR_COLOR"],
                "distance": -i * 15.0, "speed": 0.0, "lap": 0,
                "lap_distances": 0.0, "tire_wear": 0.0,
                "boost_available": True, "boost_active": 0,
                "finished": False, "finish_tick": None, "lateral": 0.0,
                "tire_compound": "medium", "tire_age_laps": 0,
                "fuel_kg": start_fuel, "max_fuel_kg": start_fuel,
                "fuel_base_rate": start_fuel / max(laps * 94, 1),
                "pit_state": create_pit_state(), "engine_mode": "standard",
                "power": car["POWER"] / 40.0, "grip": car["GRIP"] / 40.0,
                "weight": car["WEIGHT"] / 40.0, "aero": car["AERO"] / 40.0,
                "brakes": car["BRAKES"] / 40.0,
                "tire_temp": 20.0, "drs_available": True, "drs_active": False,
                "setup": car.get("setup", {}),
                "setup_raw": car.get("setup_raw", {}), "_prev_lap": 0,
            })
        self.timings = create_timing([cs["name"] for cs in self.states])
        self.sector_boundaries = (0.333, 0.666, 1.0)
        self.history, self.tick, self.race_over = [], 0, False

    def build_strategy_state(self, car_state, positions):
        """Build the state dict passed to car strategy functions."""
        cs = car_state
        nearby = [
            {"name": o["name"], "distance_ahead": o["distance"] - cs["distance"],
             "speed": o["speed"], "lateral": o["lateral"]}
            for o in self.states if o["car_idx"] != cs["car_idx"]
            and abs(o["distance"] - cs["distance"]) < 100]
        by_dist = sorted(self.states, key=lambda s: -s["distance"])
        mi = next(i for i, s in enumerate(by_dist) if s["car_idx"] == cs["car_idx"])
        gap_a = gap_b = 0.0
        if mi > 0:
            spd = by_dist[mi - 1]["speed"] * (1 / 3.6) * self.world_scale
            gap_a = (by_dist[mi - 1]["distance"] - cs["distance"]) / spd if spd > 0 else 0.0
        if mi < len(by_dist) - 1:
            spd = cs["speed"] * (1 / 3.6) * self.world_scale
            gap_b = (cs["distance"] - by_dist[mi + 1]["distance"]) / spd if spd > 0 else 0.0
        ps = cs.get("pit_state", {})
        data_file = os.path.join(self.car_data_dir, f"{cs['name']}.json") if self.car_data_dir else None
        return {
            "speed": cs["speed"], "position": positions[cs["car_idx"]],
            "total_cars": len(self.cars), "lap": cs["lap"], "total_laps": self.laps,
            "tire_wear": cs["tire_wear"], "boost_available": cs["boost_available"],
            "boost_active": cs["boost_active"] > 0,
            "curvature": get_curvature_at(
                cs["distance"], self.distances, self.curvatures, self.track_length),
            "nearby_cars": nearby, "distance": cs["distance"],
            "track_length": self.track_length, "lateral": cs["lateral"],
            "fuel_remaining": cs["fuel_kg"],
            "fuel_pct": cs["fuel_kg"] / max(cs.get("max_fuel_kg", 1.0), 0.001),
            "tire_compound": cs.get("tire_compound", "medium"),
            "tire_age_laps": cs.get("tire_age_laps", 0),
            "engine_mode": cs.get("engine_mode", "standard"),
            "pit_status": ps.get("status", "racing"), "pit_stops": ps.get("pit_stops", 0),
            "gap_ahead_s": gap_a, "gap_behind_s": gap_b, "track_name": self.track_name,
            "data_file": data_file, "race_number": self.race_number,
            "tire_temp": cs["tire_temp"], "drs_available": cs["drs_available"],
            "drs_active": cs["drs_active"], "in_drs_zone": cs.get("_in_drs_zone", False),
            "current_setup": cs.get("setup_raw", {}),
            "in_dirty_air": cs.get("_in_dirty_air", False),
            "dirty_air_factor": cs.get("_dirty_air_grip", 1.0),
            "elapsed_s": self.tick / self.TICKS_PER_SEC,
            "last_lap_time": (self.timings[cs["name"]].lap_times[-1]
                              if self.timings[cs["name"]].lap_times else None),
            "best_lap_time": self.timings[cs["name"]].best_lap,
        }

    def step(self):
        """Advance simulation by one tick."""
        if self.race_over:
            return
        positions = _compute_positions(self.states)
        dt = 1.0 / self.TICKS_PER_SEC
        for state in self.states:
            if not state["finished"]:
                self._step_car(state, positions, dt)
        self._record_frame(positions)
        self.tick += 1
        if all(s["finished"] for s in self.states):
            self.race_over = True

    def _step_car(self, state, positions, dt):
        """Advance a single car by one tick."""
        car = self.cars[state["car_idx"]]

        strat_state = self.build_strategy_state(state, positions)
        try:
            decision = car["strategy"](strat_state)
            if not isinstance(decision, dict):
                decision = {}
        except Exception:
            decision = {}

        throttle = max(0.0, min(1.0, decision.get("throttle", 1.0)))
        wants_boost = bool(decision.get("boost", False))
        tire_mode = decision.get("tire_mode", "balanced")
        lateral_target = float(decision.get("lateral_target", 0.0))
        engine_mode = decision.get("engine_mode", "standard")
        if engine_mode not in VALID_ENGINE_MODES:
            engine_mode = "standard"
        pit_request = bool(decision.get("pit_request", False))
        tire_compound_request = decision.get("tire_compound_request", None)

        state["engine_mode"] = engine_mode
        if pit_request:
            compound = tire_compound_request or state.get("tire_compound", "medium")
            state["pit_state"] = request_pit_stop(
                state["pit_state"], compound
            )
        state["pit_state"], pit_completed = update_pit_state(state["pit_state"])
        if pit_completed:
            state["pit_state"], new_compound = complete_pit_stop(state["pit_state"])
            state["tire_compound"] = new_compound
            state["tire_wear"] = 0.0
            state["tire_age_laps"] = 0

        # Dirty air: compute grip/wear penalties from following in corners
        curv = get_curvature_at(
            state["distance"], self.distances, self.curvatures, self.track_length)
        da_grip, da_wear = compute_dirty_air_factor(strat_state["gap_ahead_s"], curv)
        state["_in_dirty_air"] = da_grip < 1.0
        state["_dirty_air_grip"] = da_grip
        state["_dirty_air_wear"] = da_wear

        self._apply_boost(state, wants_boost)
        self._apply_tire_wear(state, tire_mode)
        self._apply_tire_temp_drs(state, throttle, decision, strat_state, dt)
        self._apply_physics(state, throttle, dt)
        self._apply_drafting(state, dt)
        self._apply_lateral(state, lateral_target, dt)

        if state["fuel_kg"] > 0:  # Fuel consumption
            consumed = compute_fuel_consumption(
                throttle, engine_mode, state["fuel_base_rate"], dt
            )
            state["fuel_kg"] = max(0.0, state["fuel_kg"] - consumed)

        self._update_distance(state, dt)

        # Timing update — sector/lap tracking
        dist_in_lap = state["distance"] % self.track_length
        dist_pct = dist_in_lap / self.track_length if self.track_length > 0 else 0.0
        t_result = update_timing(
            self.timings, state["name"], dist_pct, state["lap"],
            self.tick, self.TICKS_PER_SEC, self.sector_boundaries)
        state["_timing"] = t_result
        state["_gap_ahead_s"] = strat_state["gap_ahead_s"]
        state["_gap_behind_s"] = strat_state["gap_behind_s"]
        ct = self.timings[state["name"]]
        state["_last_lap_time"] = ct.lap_times[-1] if ct.lap_times else None
        state["_best_lap_s"] = ct.best_lap
        if t_result.get("sector_completed"):
            state["_last_sector_time"] = t_result["sector_time"]
            state["_last_sector_idx"] = t_result.get("current_sector", 0) - 1
        else:
            state["_last_sector_time"] = None
            state["_last_sector_idx"] = None

    def _apply_boost(self, state, wants_boost):
        """Handle boost activation and countdown."""
        if wants_boost and state["boost_available"] and state["boost_active"] == 0:
            state["boost_active"] = self.TICKS_PER_SEC * 3  # 3 seconds
            state["boost_available"] = False
        if state["boost_active"] > 0:
            state["boost_active"] -= 1

    def _apply_tire_wear(self, state, tire_mode):
        """Apply tire wear using compound model. tire_mode modulates throttle."""
        throttle_factor = {"conserve": 0.4, "balanced": 0.7, "push": 1.0}.get(tire_mode, 0.7)
        throttle_factor *= state.get("_dirty_air_wear", 1.0)  # dirty air increases wear
        curv = get_curvature_at(
            state["distance"], self.distances, self.curvatures, self.track_length)
        state["tire_wear"] = compute_wear(
            state["tire_wear"], state.get("tire_compound", "medium"), throttle_factor, curv)

    def _apply_tire_temp_drs(self, state, throttle, decision, strat_state, dt):
        """Update tire temperature and DRS activation state."""
        curv = get_curvature_at(
            state["distance"], self.distances, self.curvatures, self.track_length)
        heat = heat_generation(throttle, curv, state["lateral"], dt)
        heat *= state["setup"].get("temp_rate_mult", 1.0)
        cool = heat_dissipation(state["tire_temp"], state["speed"], dt)
        state["tire_temp"] = update_tire_temp(state["tire_temp"], heat, cool)
        dist_in_lap = state["distance"] % self.track_length
        dist_pct = dist_in_lap / self.track_length if self.track_length > 0 else 0.0
        in_zone = is_in_drs_zone(dist_pct, self.drs_zones)
        lap_changed = state["lap"] > state.get("_prev_lap", 0)
        state["_prev_lap"] = state["lap"]
        drs_requested = bool(decision.get("drs_request", False))
        state["drs_available"], state["drs_active"] = update_drs_state(
            state["drs_available"], state["drs_active"],
            drs_requested, in_zone, strat_state["gap_ahead_s"], lap_changed)
        state["_in_drs_zone"] = in_zone

    def _apply_physics(self, state, throttle, dt):
        """Calculate speed from power, grip, curvature, braking, fuel, engine."""
        setup = state.get("setup", {})
        compound = state.get("tire_compound", "medium")
        tire_grip = compute_grip_multiplier(state["tire_wear"], compound)
        temp_grip = tire_temp_grip_factor(state["tire_temp"], compound)
        dirty_grip = state.get("_dirty_air_grip", 1.0)
        power_mode = get_engine_mode(state.get("engine_mode", "standard"))["power_mult"]
        curv = get_curvature_at(
            state["distance"], self.distances, self.curvatures, self.track_length)
        # Aero grip: speed-dependent downforce bonus for corners
        wing = state.get("setup_raw", {}).get("wing_angle", 0.0)
        eff_aero = setup.get("effective_aero", state["aero"])
        aero_grip = compute_aero_grip(state["speed"], eff_aero, wing)
        target = compute_target_speed(
            power=state["power"], grip=state["grip"] + aero_grip,
            weight=state["weight"], curvature=curv, throttle=throttle,
            tire_grip_mult=tire_grip * temp_grip * dirty_grip,
            power_mode=power_mode,
            boost_active=state["boost_active"] > 0, setup=setup)
        target *= drs_speed_multiplier(state.get("_in_drs_zone", False), state["drs_active"])
        pit_st = state.get("pit_state", {})
        if pit_st and is_in_pit(pit_st):
            pit_limit = get_speed_limit(pit_st)
            if pit_limit is not None:
                target = min(target, pit_limit)
            elif pit_st.get("status") == "pit_stationary":
                target = 0
        fuel_w = compute_weight_from_fuel(state.get("fuel_kg", 0), state.get("max_fuel_kg", 1.0))
        brakes = setup.get("effective_brakes", state["brakes"])
        state["speed"] = update_speed(
            state["speed"], target, state["power"], state["weight"], fuel_w, brakes, dt)
        state["speed"] = apply_drag(state["speed"], dt)

    def _apply_drafting(self, state, dt):
        """Apply drafting speed bonus from cars ahead."""
        aero = state.get("setup", {}).get("effective_aero", state["aero"])
        for other in self.states:
            if other["car_idx"] == state["car_idx"] or other["finished"]:
                continue
            dist_ahead = other["distance"] - state["distance"]
            bonus = compute_draft_bonus(aero, dist_ahead, dt)
            state["speed"] += bonus

        # Speed can't go negative or exceed cap
        state["speed"] = max(0, min(MAX_SPEED, state["speed"]))

    def _apply_lateral(self, state, lateral_target, dt):
        """Move car laterally toward target. Faster cars are less agile."""
        lateral_target = max(-1.0, min(1.0, lateral_target))
        speed_factor = max(0.2, 1.0 - (state["speed"] / 300.0) * 0.6)
        grip_mult = tire_model.compute_grip_multiplier(
            state["tire_wear"], state.get("tire_compound", "medium"))
        rate = 2.0 * speed_factor * min(1.0, grip_mult) * dt
        state["lateral"] += (lateral_target - state["lateral"]) * rate
        state["lateral"] = max(-1.0, min(1.0, state["lateral"]))
        for other in self.states:
            if other["car_idx"] == state["car_idx"] or other["finished"]:
                continue
            dist = abs(other["distance"] - state["distance"])
            push = compute_lateral_push(
                state["lateral"] - other["lateral"], dist, dt)
            state["lateral"] = max(-1.0, min(1.0, state["lateral"] + push))

    def _update_distance(self, state, dt):
        """Update distance, check lap/finish. Pit-stationary cars don't move."""
        if state.get("pit_state", {}).get("status") == "pit_stationary":
            return
        state["distance"] += state["speed"] * (1.0 / 3.6) * self.world_scale * dt
        current_lap = int(state["distance"] / self.track_length)
        if current_lap > state["lap"]:
            state["lap"] = current_lap
            state["tire_age_laps"] = state.get("tire_age_laps", 0) + 1
        total_race_dist = self.track_length * self.laps
        if state["distance"] >= total_race_dist:
            state["finished"], state["finish_tick"] = True, self.tick
            state["distance"] = total_race_dist

    def _record_frame(self, positions):
        """Record one animation frame for replay."""
        self.history.append(record_frame(
            states=self.states, positions=positions, track=self.track,
            distances=self.distances, track_length=self.track_length,
            track_width=self.TRACK_WIDTH,
            tick=self.tick, ticks_per_sec=self.TICKS_PER_SEC))

    def run(self, max_ticks=36000):
        """Run the full race."""
        while not self.race_over and self.tick < max_ticks:
            self.step()
        return self.get_results()

    def get_results(self):
        """Get final race results."""
        return get_results(self.states, len(self.cars),
                           self.timings, self.TICKS_PER_SEC)

    def export_replay(self):
        """Export replay data as JSON-compatible dict."""
        return export_replay(
            track=self.track, track_width=self.TRACK_WIDTH,
            track_name=self.track_name, laps=self.laps,
            ticks_per_sec=self.TICKS_PER_SEC, history=self.history,
            states=self.states, num_cars=len(self.cars),
            track_curvatures=self.curvatures, track_headings=self.headings,
            timings=self.timings)
