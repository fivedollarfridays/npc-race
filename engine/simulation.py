"""Race simulation for NPC Race.

Physics simulation with tire compounds, fuel load, pit stops,
engine modes, and world-scale distance. Replay delegated to engine.replay.
"""

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

VALID_ENGINE_MODES = {"push", "standard", "conserve"}

# Physics constants (tuned for realistic lap times)
BASE_SPEED = 155           # km/h base speed at 0 power
POWER_SPEED_FACTOR = 90    # km/h added per unit of power
WEIGHT_SPEED_PENALTY = 60  # km/h lost per unit of weight
CURVATURE_FACTOR = 47.0    # Curvature-to-severity conversion
GRIP_BASE_SPEED = 60       # km/h minimum corner speed
GRIP_SPEED_RANGE = 300     # km/h range from grip
ACCEL_BASE = 50
ACCEL_POWER_FACTOR = 60
WEIGHT_MASS_FACTOR = 1.2
BRAKE_BASE = 80
BRAKE_FACTOR = 100
DRAFT_BONUS_BASE = 8
DRAFT_MAX_DISTANCE = 40


class RaceSim:
    TICKS_PER_SEC = 30
    TRACK_WIDTH = 50

    def __init__(self, cars, track_points, laps=3, seed=42, track_name=None,
                 real_length_m=None, car_data_dir=None, race_number=1):
        self.cars, self.track, self.laps = cars, track_points, laps
        self.rng, self.track_name = random.Random(seed), track_name
        self.car_data_dir = car_data_dir
        self.race_number = race_number
        self.distances, self.curvatures, self.track_length = compute_track_data(
            track_points)
        self.headings = compute_track_headings(track_points)
        self.n_points = len(track_points)
        # World_scale converts sim km/h to track units/s. Calibrated so that
        # ~160 km/h average gives ~75s laps (3333 ≈ 75s * 44.44 m/s).
        # Using real_length_m directly caused inconsistent times because sim
        # physics can't reproduce real speed variance (160 vs 260 km/h avg).
        self.world_scale = self.track_length / 3333.0
        # Calibrated equivalent distance for fuel: track_length/world_scale == 3333m always
        start_fuel = compute_starting_fuel(laps, 3333.0)
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
                "fuel_base_rate": start_fuel / (laps * 2500),
                "pit_state": create_pit_state(), "engine_mode": "standard",
                "power": car["POWER"] / 40.0, "grip": car["GRIP"] / 40.0,
                "weight": car["WEIGHT"] / 40.0, "aero": car["AERO"] / 40.0,
                "brakes": car["BRAKES"] / 40.0,
            })
        self.history, self.tick, self.race_over = [], 0, False

    def build_strategy_state(self, car_state, positions):
        """Build the state dict passed to car strategy functions."""
        cs = car_state
        nearby = [
            {"name": o["name"], "distance_ahead": o["distance"] - cs["distance"],
             "speed": o["speed"], "lateral": o["lateral"]}
            for o in self.states
            if o["car_idx"] != cs["car_idx"]
            and abs(o["distance"] - cs["distance"]) < 100
        ]
        # Compute gap to car ahead/behind
        by_dist = sorted(self.states, key=lambda s: -s["distance"])
        mi = next(i for i, s in enumerate(by_dist) if s["car_idx"] == cs["car_idx"])
        gap_a = gap_b = 0.0
        if mi > 0:
            spd = by_dist[mi - 1]["speed"] * (1 / 3.6) * self.world_scale
            if spd > 0:
                gap_a = (by_dist[mi - 1]["distance"] - cs["distance"]) / spd
        if mi < len(by_dist) - 1:
            spd = cs["speed"] * (1 / 3.6) * self.world_scale
            if spd > 0:
                gap_b = (cs["distance"] - by_dist[mi + 1]["distance"]) / spd
        ps = cs.get("pit_state", {})
        return {
            "speed": cs["speed"], "position": positions[cs["car_idx"]],
            "total_cars": len(self.cars), "lap": cs["lap"],
            "total_laps": self.laps, "tire_wear": cs["tire_wear"],
            "boost_available": cs["boost_available"],
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
            "pit_status": ps.get("status", "racing"),
            "pit_stops": ps.get("pit_stops", 0),
            "gap_ahead_s": gap_a, "gap_behind_s": gap_b,
            "track_name": self.track_name,
            "data_file": (os.path.join(self.car_data_dir, f"{cs['name']}.json")
                          if self.car_data_dir else None),
            "race_number": self.race_number,
        }

    def step(self):
        """Advance simulation by one tick."""
        if self.race_over:
            return

        positions = _compute_positions(self.states)
        dt = 1.0 / self.TICKS_PER_SEC

        for i, state in enumerate(self.states):
            if state["finished"]:
                continue
            self._step_car(state, positions, dt)

        # Record frame (reuse already-computed positions)
        self._record_frame(positions)
        self.tick += 1

        # Check if race is over
        if all(s["finished"] for s in self.states):
            self.race_over = True

    def _step_car(self, state, positions, dt):
        """Advance a single car by one tick."""
        car = self.cars[state["car_idx"]]

        # Get strategy decisions (lightweight exception guard;
        # full sandbox with timeout used at load time via car_loader)
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

        self._apply_boost(state, wants_boost)
        self._apply_tire_wear(state, tire_mode)
        self._apply_physics(state, throttle, dt)
        self._apply_drafting(state, dt)
        self._apply_lateral(state, lateral_target, dt)

        if state["fuel_kg"] > 0:  # Fuel consumption
            consumed = compute_fuel_consumption(
                throttle, engine_mode, state["fuel_base_rate"], dt
            )
            state["fuel_kg"] = max(0.0, state["fuel_kg"] - consumed)

        self._update_distance(state, dt)

    def _apply_boost(self, state, wants_boost):
        """Handle boost activation and countdown."""
        if wants_boost and state["boost_available"] and state["boost_active"] == 0:
            state["boost_active"] = self.TICKS_PER_SEC * 3  # 3 seconds
            state["boost_available"] = False
        if state["boost_active"] > 0:
            state["boost_active"] -= 1

    def _apply_tire_wear(self, state, tire_mode):
        """Apply tire wear using compound model. tire_mode modulates throttle."""
        throttle_map = {"conserve": 0.4, "balanced": 0.7, "push": 1.0}
        throttle_factor = throttle_map.get(tire_mode, 0.7)
        compound = state.get("tire_compound", "medium")
        curv = get_curvature_at(
            state["distance"], self.distances,
            self.curvatures, self.track_length,
        )
        state["tire_wear"] = compute_wear(
            state["tire_wear"], compound, throttle_factor, curv
        )

    def _apply_physics(self, state, throttle, dt):
        """Calculate speed from power, grip, curvature, braking, fuel, engine."""
        power, grip = state["power"], state["grip"]
        weight, brakes = state["weight"], state["brakes"]
        tire_grip_mult = compute_grip_multiplier(
            state["tire_wear"], state.get("tire_compound", "medium")
        )
        power_mode = get_engine_mode(state.get("engine_mode", "standard"))["power_mult"]
        base_max_speed = (BASE_SPEED + power * POWER_SPEED_FACTOR * power_mode
                         - weight * WEIGHT_SPEED_PENALTY)
        if state["boost_active"] > 0:
            base_max_speed *= 1.25
        curv = get_curvature_at(
            state["distance"], self.distances,
            self.curvatures, self.track_length,
        )
        effective_grip = grip * tire_grip_mult
        curv_severity = min(1.0, curv * CURVATURE_FACTOR)
        grip_speed = GRIP_BASE_SPEED + effective_grip * GRIP_SPEED_RANGE
        target_speed = (
            base_max_speed * (1.0 - curv_severity)
            + grip_speed * curv_severity
        ) * throttle
        target_speed = max(40, target_speed)
        pit_st = state.get("pit_state", {})
        if pit_st and is_in_pit(pit_st):
            pit_limit = get_speed_limit(pit_st)
            if pit_limit is not None:
                target_speed = min(target_speed, pit_limit)
            elif pit_st.get("status") == "pit_stationary":
                target_speed = 0
        fuel_weight = compute_weight_from_fuel(
            state.get("fuel_kg", 0), state.get("max_fuel_kg", 1.0)
        )
        mass_factor = 1.0 + weight * WEIGHT_MASS_FACTOR + fuel_weight
        accel_rate = (ACCEL_BASE + power * ACCEL_POWER_FACTOR) / mass_factor * dt
        brake_rate = (BRAKE_BASE + brakes * BRAKE_FACTOR) * dt
        if target_speed > state["speed"]:
            state["speed"] = min(target_speed, state["speed"] + accel_rate)
        else:
            state["speed"] = max(target_speed, state["speed"] - brake_rate)

    def _apply_drafting(self, state, dt):
        """Apply drafting speed bonus from cars ahead."""
        aero = state["aero"]
        for other in self.states:
            if other["car_idx"] == state["car_idx"] or other["finished"]:
                continue
            dist_ahead = other["distance"] - state["distance"]
            if 5 < dist_ahead < DRAFT_MAX_DISTANCE:
                draft_bonus = (aero * DRAFT_BONUS_BASE
                               * (1 - dist_ahead / DRAFT_MAX_DISTANCE))
                state["speed"] += draft_bonus * dt

        # Speed can't go negative
        state["speed"] = max(0, state["speed"])

    def _apply_lateral(self, state, lateral_target, dt):
        """Move car laterally toward target. Faster cars are less agile."""
        lateral_target = max(-1.0, min(1.0, lateral_target))
        base_rate = 2.0
        speed_factor = max(0.2, 1.0 - (state["speed"] / 300.0) * 0.6)
        grip_mult = tire_model.compute_grip_multiplier(
            state["tire_wear"], state.get("tire_compound", "medium")
        )

        rate = base_rate * speed_factor * min(1.0, grip_mult) * dt
        diff = lateral_target - state["lateral"]
        state["lateral"] += diff * rate
        state["lateral"] = max(-1.0, min(1.0, state["lateral"]))

        for other in self.states:  # Proximity resistance
            if other["car_idx"] == state["car_idx"] or other["finished"]:
                continue
            dist = abs(other["distance"] - state["distance"])
            if dist < 10:
                lat_diff = state["lateral"] - other["lateral"]
                if abs(lat_diff) < 0.3:
                    push = 0.1 * (1.0 - dist / 10) * dt
                    if lat_diff >= 0:
                        state["lateral"] = min(1.0, state["lateral"] + push)
                    else:
                        state["lateral"] = max(-1.0, state["lateral"] - push)

    def _update_distance(self, state, dt):
        """Update distance, check lap/finish. Pit-stationary cars don't move."""
        if state.get("pit_state", {}).get("status") == "pit_stationary":
            return

        state["distance"] += state["speed"] * (1.0 / 3.6) * self.world_scale * dt

        total_race_dist = self.track_length * self.laps
        current_lap = int(state["distance"] / self.track_length)
        if current_lap > state["lap"]:
            state["lap"] = current_lap
            state["tire_age_laps"] = state.get("tire_age_laps", 0) + 1

        if state["distance"] >= total_race_dist:
            state["finished"] = True
            state["finish_tick"] = self.tick
            state["distance"] = total_race_dist

    def _record_frame(self, positions):
        """Record one animation frame for replay."""
        frame = record_frame(
            states=self.states,
            positions=positions,
            track=self.track,
            distances=self.distances,
            track_length=self.track_length,
            track_width=self.TRACK_WIDTH,
        )
        self.history.append(frame)

    def run(self, max_ticks=36000):
        """Run the full race."""
        while not self.race_over and self.tick < max_ticks:
            self.step()
        return self.get_results()

    def get_results(self):
        """Get final race results."""
        return get_results(self.states, len(self.cars))

    def export_replay(self):
        """Export replay data as JSON-compatible dict."""
        return export_replay(
            track=self.track,
            track_width=self.TRACK_WIDTH,
            track_name=self.track_name,
            laps=self.laps,
            ticks_per_sec=self.TICKS_PER_SEC,
            history=self.history,
            states=self.states,
            num_cars=len(self.cars),
            track_curvatures=self.curvatures,
            track_headings=self.headings,
        )
