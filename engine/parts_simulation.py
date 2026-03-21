"""Parts-based race simulation — cars driven by player-coded part functions.

Replaces the old stat-based simulation with the parts runner.
Each tick, all 10 part functions are called for each car.
"""

import random

from .track_gen import compute_track_data, compute_track_headings, get_curvature_at
from .replay import record_frame, get_results, export_replay, _compute_positions
from .parts_api import get_defaults, get_hardware_spec
from .parts_runner import create_initial_state, run_parts_tick  # noqa: F401
from .efficiency_engine import run_efficiency_tick
from .driver_model import create_driver, compute_driver_inputs


class PartsRaceSim:
    """Race simulation driven by player-coded part functions."""

    TICKS_PER_SEC = 30
    TRACK_WIDTH = 50

    def __init__(self, cars, track_points, laps=3, seed=42, track_name=None,
                 real_length_m=None):
        self.cars = cars
        self.track = track_points
        self.laps = laps
        self.rng = random.Random(seed)
        self.track_name = track_name
        self.distances, self.curvatures, self.track_length = compute_track_data(track_points)
        self.headings = compute_track_headings(track_points)

        if real_length_m and real_length_m > 0:
            self.world_scale = self.track_length / real_length_m
        else:
            self.world_scale = self.track_length / 5000.0

        # Build hardware specs for each car
        self.car_states = []
        self.car_parts = []
        self.drivers = []
        self.call_logs = []  # per-tick call logs for live terminal
        defaults = get_defaults()

        for i, car in enumerate(cars):
            # Get hardware specs
            engine_spec = get_hardware_spec("ENGINE_SPEC", car.get("engine_spec", "v6_1000hp")) or {}
            aero_spec = get_hardware_spec("AERO_SPEC", car.get("aero_spec", "medium_downforce")) or {}
            chassis_spec = get_hardware_spec("CHASSIS_SPEC", car.get("chassis_spec", "standard")) or {}
            hw = {**engine_spec, **aero_spec, **chassis_spec}

            # Create car state
            state = create_initial_state(hw)
            state["name"] = car["CAR_NAME"]
            state["color"] = car["CAR_COLOR"]
            state["car_idx"] = i
            state["distance"] = -i * 15.0
            state["laps_total"] = laps
            state["finished"] = False
            state["finish_tick"] = None
            state.setdefault("position", i + 1)
            state.setdefault("gap_ahead", 0)
            self.car_states.append(state)

            # Get part functions
            parts = car.get("parts", defaults)
            self.car_parts.append(parts)

            # Create driver model
            car_stats = {"power": hw.get("max_hp", 1000) / 2000,
                         "grip": aero_spec.get("base_cl", 4.5) / 10,
                         "weight": chassis_spec.get("weight_kg", 798) / 1600}
            driver = create_driver(track_points, self.curvatures, self.distances,
                                   self.headings, self.track_length, car_stats,
                                   real_length_m=real_length_m or 5793)
            self.drivers.append(driver)

        self.prev_states = [None] * len(cars)
        self.history = []
        self.tick = 0
        self.race_over = False

    def step(self):
        """Advance simulation by one tick."""
        if self.race_over:
            return
        dt = 1.0 / self.TICKS_PER_SEC
        tick_logs = []

        for i, state in enumerate(self.car_states):
            if state["finished"]:
                continue

            # Driver model provides throttle demand and lateral target
            driver = self.drivers[i]
            driver_inputs = compute_driver_inputs(
                driver, state, state.get("tire_wear", 0),
                0.0, 0.0)

            # Compute curvature at current position
            curv = get_curvature_at(state["distance"], self.distances,
                                     self.curvatures, self.track_length)

            # Brake when speed exceeds profile target
            from .speed_profile import get_profile_speed
            profile_speed = get_profile_speed(
                driver["profile"], state["distance"], self.distances, self.track_length)
            # Part outputs affect achievable corner speed through grip
            if curv > 0.005:
                grip_factor = state.get("grip_factor", 1.0)
                profile_speed *= grip_factor
            is_braking = state["speed_kmh"] > profile_speed * 1.02
            corner_phase = "straight"
            if curv > 0.02:
                corner_phase = "mid"
            elif curv > 0.005:
                corner_phase = "entry"

            physics = {
                "curvature": curv,
                "corner_phase": corner_phase,
                "lateral_g": curv * state["speed_kmh"] / 150,
                "bump_severity": 0.0,
                "weather_wetness": 0.0,
                "throttle_demand": driver_inputs["throttle"],
                "target_speed": profile_speed,
                "braking": is_braking,
            }

            # Get hardware specs
            engine_spec = get_hardware_spec("ENGINE_SPEC",
                                            self.cars[i].get("engine_spec", "v6_1000hp")) or {}
            aero_spec = get_hardware_spec("AERO_SPEC",
                                          self.cars[i].get("aero_spec", "medium_downforce")) or {}
            chassis_spec = get_hardware_spec("CHASSIS_SPEC",
                                             self.cars[i].get("chassis_spec", "standard")) or {}
            hw = {**engine_spec, **aero_spec, **chassis_spec}

            # Run all 10 parts via efficiency engine
            new_state, log, efficiency_product = run_efficiency_tick(
                self.car_parts[i], state, physics, hw, dt, self.tick,
                prev_state=self.prev_states[i])
            self.prev_states[i] = dict(state)  # snapshot for next tick's t-1
            new_state["efficiency_product"] = efficiency_product

            # Update distance
            speed_ms = new_state["speed_kmh"] / 3.6
            new_state["distance"] = state["distance"] + speed_ms * self.world_scale * dt

            # Lateral from driver
            new_state["lateral"] = state.get("lateral", 0.0)
            lat_target = driver_inputs.get("lateral_target", 0.0)
            rate = 0.05
            new_state["lateral"] += (lat_target - new_state["lateral"]) * rate

            # Check lap/finish
            current_lap = int(new_state["distance"] / self.track_length)
            if current_lap > state.get("lap", 0):
                new_state["lap"] = current_lap
            total_dist = self.track_length * self.laps
            if new_state["distance"] >= total_dist:
                new_state["finished"] = True
                new_state["finish_tick"] = self.tick
                new_state["distance"] = total_dist

            # Copy back
            self.car_states[i] = new_state
            tick_logs.extend(log)

        self.call_logs.append(tick_logs)

        # Record frame for replay
        positions = _compute_positions(self._to_legacy_states())
        self.history.append(record_frame(
            states=self._to_legacy_states(), positions=positions,
            track=self.track, distances=self.distances,
            track_length=self.track_length, track_width=self.TRACK_WIDTH,
            tick=self.tick, ticks_per_sec=self.TICKS_PER_SEC))

        self.tick += 1
        if all(s["finished"] for s in self.car_states):
            self.race_over = True

    def _to_legacy_states(self):
        """Convert parts car states to legacy format for replay recording."""
        legacy = []
        for s in self.car_states:
            legacy.append({
                "car_idx": s.get("car_idx", 0),
                "name": s.get("name", "Unknown"),
                "color": s.get("color", "#ffffff"),
                "distance": s.get("distance", 0),
                "speed": s.get("speed_kmh", 0),
                "lap": s.get("lap", 0),
                "tire_wear": s.get("tire_wear", 0),
                "boost_active": 0,
                "finished": s.get("finished", False),
                "finish_tick": s.get("finish_tick"),
                "lateral": s.get("lateral", 0),
                "tire_compound": s.get("tire_compound", "medium"),
                "tire_age_laps": 0,
                "fuel_kg": s.get("fuel_remaining_kg", 110),
                "max_fuel_kg": s.get("fuel_capacity_kg", 110),
                "pit_state": {"status": "racing", "pit_stops": s.get("pit_stops", 0)},
                "engine_mode": "standard",
                "tire_temp": s.get("engine_temp", 90),
                "drs_available": False,
                "drs_active": False,
                "damage": {"damage": 0, "dnf": False},
                "spin_recovery": 0,
                "contact_cooldown": 0,
                "brake_state": {"temp": s.get("brake_temp", 400)},
                "ers": {"energy": s.get("ers_state", {}).get("energy_mj", 4.0)},
                "ers_deploy_mode": "balanced",
                "_safety_car": False,
                "_track_wetness": 0.0,
                "_dirty_air_grip": 1.0,
                "_in_dirty_air": False,
                "_gap_ahead_s": 0,
                "_gap_behind_s": 0,
                "_last_lap_time": None,
                "_best_lap_s": None,
                "_last_sector_time": None,
                "_last_sector_idx": None,
                "_spin_risk": 0,
                "_timing": {},
            })
        return legacy

    def run(self, max_ticks=36000):
        """Run the full race."""
        while not self.race_over and self.tick < max_ticks:
            self.step()
        return self.get_results()

    def get_results(self):
        """Get race results."""
        return get_results(self._to_legacy_states(), len(self.cars))

    def export_replay(self):
        """Export replay data."""
        return export_replay(
            track=self.track, track_width=self.TRACK_WIDTH,
            track_name=self.track_name, laps=self.laps,
            ticks_per_sec=self.TICKS_PER_SEC, history=self.history,
            states=self._to_legacy_states(), num_cars=len(self.cars),
            track_curvatures=self.curvatures, track_headings=self.headings)
