"""Race simulation: compounds, fuel, pits, engine modes, collisions, SC."""
import random
from . import tire_model, sim_step
from .track_gen import compute_track_data, compute_track_headings, CurvatureLookup
from .replay import record_frame, get_results, export_replay, _compute_positions
from .tire_model import compute_grip_multiplier
from .fuel_model import compute_starting_fuel, compute_weight_from_fuel, get_engine_mode
from .pit_lane import create_pit_state, is_in_pit, get_speed_limit
from .tire_temperature import tire_temp_grip_factor
from .drs_system import drs_speed_multiplier
from .physics import compute_target_speed, compute_draft_bonus, update_speed, compute_lateral_push, apply_drag, MAX_SPEED, compute_aero_grip
from .timing import create_timing
from .damage import create_damage_state, compute_damage_penalties
from .safety_car import create_sc_state, get_sc_speed_limit
from .weather_model import create_weather_state, get_wetness_grip_mult
from .drama import process_collisions, update_step_systems
from .ers_model import create_ers_state, get_ers_speed_bonus, reset_ers_lap
from .brake_model import create_brake_state, get_brake_efficiency
from .driver_model import create_driver
from .spatial import SortedCarIndex
from .lap_accumulator import LapAccumulator

VALID_ENGINE_MODES = {"push", "standard", "conserve"}


def _create_car_state(i, car, start_fuel, laps):
    """Build initial state dict for one car."""
    return {
        "car_idx": i, "name": car["CAR_NAME"], "color": car["CAR_COLOR"],
        "distance": -i * 15.0, "speed": 0.0, "lap": 0,
        "lap_distances": 0.0, "tire_wear": 0.0,
        "boost_available": True, "boost_active": 0,
        "finished": False, "finish_tick": None, "lateral": 0.0,
        "tire_compound": "medium", "tire_age_laps": 0,
        "fuel_kg": start_fuel, "max_fuel_kg": start_fuel,
        "fuel_base_rate": start_fuel / max(laps * 2100, 1),
        "pit_state": create_pit_state(), "engine_mode": "standard",
        "power": car["POWER"] / 40.0, "grip": car["GRIP"] / 40.0,
        "weight": car["WEIGHT"] / 40.0, "aero": car["AERO"] / 40.0,
        "brakes": car["BRAKES"] / 40.0,
        "tire_temp": 20.0, "drs_available": True, "drs_active": False,
        "setup": car.get("setup", {}),
        "setup_raw": car.get("setup_raw", {}), "_prev_lap": 0,
        "damage": create_damage_state(),
        "spin_recovery": 0, "contact_cooldown": 0,
        "ers": create_ers_state(), "ers_deploy_mode": "balanced",
        "brake_state": create_brake_state(),
        "_cached_decision": {},
    }


class RaceSim:
    TICKS_PER_SEC = 30
    TRACK_WIDTH = 50

    def __init__(self, cars, track_points, laps=3, seed=42, track_name=None,
                 real_length_m=None, car_data_dir=None, race_number=1,
                 drs_zones=None, fast_mode=False):
        self.cars, self.track, self.laps = cars, track_points, laps
        self.rng, self.track_name = random.Random(seed), track_name
        self.car_data_dir = car_data_dir
        self.race_number = race_number
        self.drs_zones = drs_zones or []
        self.distances, self.curvatures, self.track_length = compute_track_data(
            track_points)
        self.curvature_lookup = CurvatureLookup(
            self.distances, self.curvatures, self.track_length)
        self.headings = compute_track_headings(track_points)
        self.n_points = len(track_points)
        if real_length_m and real_length_m > 0:
            self.world_scale = self.track_length / real_length_m
        else:
            self.world_scale = self.track_length / 5000.0  # fallback
        rlm = real_length_m if real_length_m and real_length_m > 0 else 5000.0
        start_fuel = compute_starting_fuel(laps, rlm)
        self.states = [_create_car_state(i, car, start_fuel, laps)
                       for i, car in enumerate(cars)]
        self.timings = create_timing([cs["name"] for cs in self.states])
        self.sector_boundaries = (0.333, 0.666, 1.0)
        self.safety_car = create_sc_state()
        self._sc_last_leader_lap = -1
        self.weather = create_weather_state()
        self._weather_forecast = []
        # Create F1 driver for each car
        self.drivers = {}
        for cs in self.states:
            self.drivers[cs["name"]] = create_driver(
                track_points, self.curvatures, self.distances, self.headings,
                self.track_length, {"power": cs["power"], "grip": cs["grip"],
                                     "weight": cs["weight"]})
        self.fast_mode = fast_mode
        self.accumulator = LapAccumulator() if fast_mode else None
        self.history, self.tick, self.race_over = [], 0, False

    def build_strategy_state(self, car_state, positions):
        """Build state dict for car strategy functions (delegates to sim_step)."""
        return sim_step.build_strategy_state(
            car_state=car_state, all_states=self.states,
            timings=self.timings, tick=self.tick,
            ticks_per_sec=self.TICKS_PER_SEC, distances=self.distances,
            curvature_lookup=self.curvature_lookup,
            track_length=self.track_length,
            sector_boundaries=self.sector_boundaries,
            world_scale=self.world_scale, track_name=self.track_name,
            car_data_dir=self.car_data_dir, race_number=self.race_number,
            total_laps=self.laps, drs_zones=self.drs_zones,
            safety_car_state=self.safety_car,
            weather_state=self.weather,
            weather_forecast=self._weather_forecast,
            positions=positions)

    def step(self):
        """Advance simulation by one tick."""
        if self.race_over:
            return
        positions = _compute_positions(self.states)
        spatial_index = SortedCarIndex(self.states)
        self._current_positions = positions
        self._current_spatial_index = spatial_index
        for state in self.states:
            if not state["finished"]:
                sim_step.step_car(state, self.cars[state["car_idx"]], self)
        self.states, self.safety_car = process_collisions(
            self.states, self.rng, self.safety_car, self.tick)
        self.safety_car, self.weather, self._weather_forecast, self._sc_last_leader_lap = (
            update_step_systems(self.states, self.safety_car, self.weather,
                                self.rng, self._sc_last_leader_lap,
                                self._weather_forecast))
        if self.fast_mode:
            name_positions = {s["name"]: positions[s["car_idx"]] for s in self.states}
            self.accumulator.on_tick(self.states, name_positions, self.tick)
            self._detect_lap_completions()
            if self.tick % self.TICKS_PER_SEC == 0:
                self._record_frame(positions)
        else:
            self._record_frame(positions)
        self.tick += 1
        if all(s["finished"] for s in self.states):
            self.race_over = True

    def _compute_gap_ahead_s(self, state):
        """Lightweight gap_ahead_s for dirty air (computed every tick)."""
        by_dist = sorted(self.states, key=lambda s: -s["distance"])
        mi = next(i for i, s in enumerate(by_dist) if s["car_idx"] == state["car_idx"])
        if mi > 0:
            spd = by_dist[mi - 1]["speed"] * (1 / 3.6) * self.world_scale
            return (by_dist[mi - 1]["distance"] - state["distance"]) / spd if spd > 0 else 0.0
        return 0.0

    def _apply_physics(self, state, throttle, dt):
        """Calculate speed from power, grip, curvature, braking, fuel, engine, damage, SC."""
        setup, compound = state.get("setup", {}), state.get("tire_compound", "medium")
        grip_mult = (compute_grip_multiplier(state["tire_wear"], compound) * tire_temp_grip_factor(state["tire_temp"], compound)
                     * state.get("_dirty_air_grip", 1.0) * get_wetness_grip_mult(self.weather.get("wetness", 0.0), compound))
        curv = self.curvature_lookup[state["distance"]]
        eff_aero = setup.get("effective_aero", state["aero"] * 40.0) / 40.0
        aero_grip = compute_aero_grip(state["speed"], eff_aero,
                                       state.get("setup_raw", {}).get("wing_angle", 0.0))
        target = compute_target_speed(
            power=state["power"], grip=state["grip"] + aero_grip, weight=state["weight"],
            curvature=curv, throttle=throttle, tire_grip_mult=grip_mult,
            power_mode=get_engine_mode(state.get("engine_mode", "standard"))["power_mult"],
            boost_active=state["boost_active"] > 0, setup=setup)
        target += get_ers_speed_bonus(state["ers"], state["ers_deploy_mode"])
        target *= drs_speed_multiplier(state.get("_in_drs_zone", False), state["drs_active"])
        target *= compute_damage_penalties(state["damage"]["damage"])["speed_mult"]
        sc_limit = get_sc_speed_limit(self.safety_car)
        if sc_limit is not None:
            target = min(target, sc_limit)
        pit_st = state.get("pit_state", {})
        if pit_st and is_in_pit(pit_st):
            pit_limit = get_speed_limit(pit_st)
            if pit_limit is not None:
                target = min(target, pit_limit)
            elif pit_st.get("status") == "pit_stationary":
                target = 0
        fuel_w = compute_weight_from_fuel(state.get("fuel_kg", 0), state.get("max_fuel_kg", 1.0))
        brakes = setup.get("effective_brakes", state["brakes"]) * get_brake_efficiency(state["brake_state"]["temp"])
        state["speed"] = update_speed(state["speed"], target, state["power"], state["weight"], fuel_w, brakes, dt)
        state["speed"] = apply_drag(state["speed"], dt)

    def _apply_drafting(self, state, dt, spatial_index=None):
        """Apply drafting speed bonus from nearby cars ahead."""
        aero = state.get("setup", {}).get("effective_aero", state["aero"] * 40.0) / 40.0
        neighbors = (spatial_index.neighbors(state["car_idx"], max_distance=40.0)
                     if spatial_index else
                     [o for o in self.states
                      if o["car_idx"] != state["car_idx"] and not o["finished"]])
        for other in neighbors:
            dist_ahead = other["distance"] - state["distance"]
            bonus = compute_draft_bonus(aero, dist_ahead, dt)
            state["speed"] += bonus

        # Speed can't go negative or exceed cap
        state["speed"] = max(0, min(MAX_SPEED, state["speed"]))

    def _apply_lateral(self, state, lateral_target, dt, spatial_index=None):
        """Move car laterally toward target. Faster cars are less agile."""
        lateral_target = max(-1.0, min(1.0, lateral_target))
        speed_factor = max(0.2, 1.0 - (state["speed"] / 300.0) * 0.6)
        grip_mult = tire_model.compute_grip_multiplier(
            state["tire_wear"], state.get("tire_compound", "medium"))
        rate = 2.0 * speed_factor * min(1.0, grip_mult) * dt
        state["lateral"] += (lateral_target - state["lateral"]) * rate
        state["lateral"] = max(-1.0, min(1.0, state["lateral"]))
        neighbors = (spatial_index.neighbors(state["car_idx"], max_distance=10.0)
                     if spatial_index else
                     [o for o in self.states
                      if o["car_idx"] != state["car_idx"] and not o["finished"]])
        for other in neighbors:
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
            state["ers"] = reset_ers_lap(state["ers"])
        total_race_dist = self.track_length * self.laps
        if state["distance"] >= total_race_dist:
            state["finished"], state["finish_tick"] = True, self.tick
            state["distance"] = total_race_dist

    def _detect_lap_completions(self):
        """Feed lap completions to accumulator (fast_mode only)."""
        for state in self.states:
            ct = self.timings[state["name"]]
            n_laps = len(ct.lap_times)
            prev = state.get("_acc_laps_reported", 0)
            if n_laps > prev:
                for i in range(prev, n_laps):
                    self.accumulator.on_lap_complete(
                        state["name"], i + 1, ct.lap_times[i])
                state["_acc_laps_reported"] = n_laps

    def get_lap_summaries(self) -> dict[str, list[dict]]:
        """Return per-car lap summaries (fast_mode only)."""
        if self.accumulator is None:
            return {}
        return self.accumulator.get_lap_summaries()

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
