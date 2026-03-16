"""
Race simulation for NPC Race.

Contains the RaceSim class that runs the physics simulation,
handles car strategy calls, and produces replay data.
"""

import math
import random

from .track_gen import compute_track_data


class RaceSim:
    TICKS_PER_SEC = 30
    TRACK_WIDTH = 50

    def __init__(self, cars, track_points, laps=3, seed=42, track_name=None):
        self.cars = cars
        self.track = track_points
        self.laps = laps
        self.rng = random.Random(seed)
        self.track_name = track_name

        self.distances, self.curvatures, self.track_length = compute_track_data(
            track_points
        )
        self.n_points = len(track_points)

        # Init car states
        self.states = []
        for i, car in enumerate(cars):
            self.states.append({
                "car_idx": i,
                "name": car["CAR_NAME"],
                "color": car["CAR_COLOR"],
                "distance": -i * 15.0,  # staggered grid start
                "speed": 0.0,
                "lap": 0,
                "lap_distances": 0.0,
                "tire_wear": 0.0,       # 0 = fresh, 1 = destroyed
                "boost_available": True,
                "boost_active": 0,       # ticks remaining
                "finished": False,
                "finish_tick": None,
                "lateral": 0.0,          # -1 to 1, lane position
                # Stats normalized to 0-1 range
                "power": car["POWER"] / 40.0,
                "grip": car["GRIP"] / 40.0,
                "weight": car["WEIGHT"] / 40.0,
                "aero": car["AERO"] / 40.0,
                "brakes": car["BRAKES"] / 40.0,
            })

        self.history = []
        self.tick = 0
        self.race_over = False

    def get_track_pos(self, distance):
        """Get x,y position on track from distance traveled."""
        d = distance % self.track_length
        if d < 0:
            d += self.track_length

        for i in range(len(self.distances) - 1):
            if self.distances[i] <= d <= self.distances[i + 1]:
                seg_len = self.distances[i + 1] - self.distances[i]
                if seg_len < 0.001:
                    t = 0
                else:
                    t = (d - self.distances[i]) / seg_len
                x = self.track[i][0] + t * (self.track[i + 1][0] - self.track[i][0])
                y = self.track[i][1] + t * (self.track[i + 1][1] - self.track[i][1])
                return x, y, i

        # Wrap around
        return self.track[0][:2] + (0,)

    def get_curvature_at(self, distance):
        """Get track curvature at a distance."""
        d = distance % self.track_length
        if d < 0:
            d += self.track_length
        for i in range(len(self.distances) - 1):
            if self.distances[i] <= d <= self.distances[i + 1]:
                return self.curvatures[i]
        return 0.0

    def get_positions(self):
        """Return sorted positions (1st, 2nd, etc.)"""
        ranked = sorted(self.states, key=lambda s: (
            -s["lap"],
            -s["distance"] if not s["finished"] else 0,
            s["finish_tick"] or float("inf")
        ))
        positions = {}
        for pos, s in enumerate(ranked):
            positions[s["car_idx"]] = pos + 1
        return positions

    def build_strategy_state(self, car_state, positions):
        """Build the state dict passed to car strategy functions."""
        pos = positions[car_state["car_idx"]]
        nearby = []
        for other in self.states:
            if other["car_idx"] == car_state["car_idx"]:
                continue
            dist_diff = other["distance"] - car_state["distance"]
            if abs(dist_diff) < 100:
                nearby.append({
                    "name": other["name"],
                    "distance_ahead": dist_diff,
                    "speed": other["speed"],
                    "lateral": other["lateral"],
                })

        return {
            "speed": car_state["speed"],
            "position": pos,
            "total_cars": len(self.cars),
            "lap": car_state["lap"],
            "total_laps": self.laps,
            "tire_wear": car_state["tire_wear"],
            "boost_available": car_state["boost_available"],
            "boost_active": car_state["boost_active"] > 0,
            "curvature": self.get_curvature_at(car_state["distance"]),
            "nearby_cars": nearby,
            "distance": car_state["distance"],
            "track_length": self.track_length,
            "lateral": car_state["lateral"],
        }

    def step(self):
        """Advance simulation by one tick."""
        if self.race_over:
            return

        positions = self.get_positions()
        dt = 1.0 / self.TICKS_PER_SEC

        for i, state in enumerate(self.states):
            if state["finished"]:
                continue
            self._step_car(state, positions, dt)

        # Record frame
        self._record_frame()
        self.tick += 1

        # Check if race is over
        if all(s["finished"] for s in self.states):
            self.race_over = True

    def _step_car(self, state, positions, dt):
        """Advance a single car by one tick."""
        car = self.cars[state["car_idx"]]

        # Get strategy decisions
        try:
            strat_state = self.build_strategy_state(state, positions)
            decision = car["strategy"](strat_state)
            if not isinstance(decision, dict):
                decision = {}
        except Exception:
            decision = {}

        throttle = max(0.0, min(1.0, decision.get("throttle", 1.0)))
        wants_boost = bool(decision.get("boost", False))
        tire_mode = decision.get("tire_mode", "balanced")

        self._apply_boost(state, wants_boost)
        self._apply_tire_wear(state, tire_mode)
        self._apply_physics(state, throttle, dt)
        self._apply_drafting(state, dt)
        self._update_distance(state, dt)

    def _apply_boost(self, state, wants_boost):
        """Handle boost activation and countdown."""
        if wants_boost and state["boost_available"] and state["boost_active"] == 0:
            state["boost_active"] = self.TICKS_PER_SEC * 3  # 3 seconds
            state["boost_available"] = False
        if state["boost_active"] > 0:
            state["boost_active"] -= 1

    def _apply_tire_wear(self, state, tire_mode):
        """Apply tire wear based on tire mode."""
        wear_rates = {"conserve": 0.00008, "balanced": 0.00018, "push": 0.00035}
        wear_rate = wear_rates.get(tire_mode, 0.0001)
        state["tire_wear"] = min(1.0, state["tire_wear"] + wear_rate)

    def _apply_physics(self, state, throttle, dt):
        """Calculate speed from power, grip, curvature, and braking."""
        power = state["power"]
        grip = state["grip"]
        weight = state["weight"]
        brakes = state["brakes"]

        # Tire wear affects grip
        tire_grip_mult = max(0.3, 1.0 - state["tire_wear"] * 0.7)

        # Max speed from power (lighter = faster)
        base_max_speed = 120 + power * 160 - weight * 50
        if state["boost_active"] > 0:
            base_max_speed *= 1.25

        # Corner speed limit — blend between power (straights) and grip (corners)
        curv = self.get_curvature_at(state["distance"])
        effective_grip = grip * tire_grip_mult
        # Linear blend: grip-biased so power/grip tradeoff matters
        curv_severity = min(1.0, curv * 47.0)
        grip_speed = 50 + effective_grip * 280  # wider grip range
        # On straights: power dominates. In corners: grip dominates.
        target_speed = (
            base_max_speed * (1.0 - curv_severity)
            + grip_speed * curv_severity
        ) * throttle
        target_speed = max(40, target_speed)

        # Acceleration / braking — weight matters more
        mass_factor = 1.0 + weight * 1.2
        accel_rate = (40 + power * 100) / mass_factor * dt
        brake_rate = (80 + brakes * 100) * dt

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
            if 5 < dist_ahead < 40:
                draft_bonus = aero * 8 * (1 - dist_ahead / 40)
                state["speed"] += draft_bonus * dt

        # Speed can't go negative
        state["speed"] = max(0, state["speed"])

    def _update_distance(self, state, dt):
        """Update distance and check for lap/finish."""
        state["distance"] += state["speed"] * dt

        # Lap counting
        total_race_dist = self.track_length * self.laps
        current_lap = int(state["distance"] / self.track_length)
        if current_lap > state["lap"]:
            state["lap"] = current_lap

        if state["distance"] >= total_race_dist:
            state["finished"] = True
            state["finish_tick"] = self.tick
            state["distance"] = total_race_dist

    def _record_frame(self):
        """Record one animation frame for replay."""
        frame = []
        positions = self.get_positions()
        for state in self.states:
            x, y, seg = self.get_track_pos(state["distance"])
            # Lateral offset
            if seg < len(self.track) - 1:
                dx = self.track[seg + 1][0] - self.track[seg][0]
                dy = self.track[seg + 1][1] - self.track[seg][1]
            else:
                dx = self.track[0][0] - self.track[seg][0]
                dy = self.track[0][1] - self.track[seg][1]
            length = math.sqrt(dx * dx + dy * dy) + 0.001
            nx, ny = -dy / length, dx / length
            lat_offset = state["lateral"] * self.TRACK_WIDTH * 0.4
            x += nx * lat_offset
            y += ny * lat_offset

            frame.append({
                "x": round(x, 1),
                "y": round(y, 1),
                "name": state["name"],
                "color": state["color"],
                "speed": round(state["speed"], 1),
                "lap": state["lap"],
                "position": positions[state["car_idx"]],
                "tire_wear": round(state["tire_wear"], 2),
                "boost": state["boost_active"] > 0,
                "finished": state["finished"],
            })

        self.history.append(frame)

    def run(self, max_ticks=10000):
        """Run the full race."""
        while not self.race_over and self.tick < max_ticks:
            self.step()
        return self.get_results()

    def get_results(self):
        """Get final race results."""
        positions = self.get_positions()
        results = []
        for state in self.states:
            results.append({
                "name": state["name"],
                "color": state["color"],
                "position": positions[state["car_idx"]],
                "finish_tick": state["finish_tick"],
                "finished": state["finished"],
            })
        results.sort(key=lambda r: r["position"])
        return results

    def export_replay(self):
        """Export replay data as JSON."""
        track_xy = [{"x": round(p[0], 1), "y": round(p[1], 1)} for p in self.track]
        return {
            "track": track_xy,
            "track_width": self.TRACK_WIDTH,
            "track_name": self.track_name,
            "laps": self.laps,
            "ticks_per_sec": self.TICKS_PER_SEC,
            "frames": self.history,
            "results": self.get_results(),
            "car_count": len(self.cars),
        }
