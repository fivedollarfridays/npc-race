"""
NPC Race Engine
===============
The world is built. The track is set. You just bring the car.

Everyone gets the same driver AI. The difference is your car:
- How you allocate your 100-point budget across POWER, GRIP, WEIGHT, AERO, BRAKES
- Your strategy() function that controls throttle, boost, and tire mode each tick

The engine handles physics, collisions, drafting, tire degradation, and produces
a replay JSON that the HTML viewer can animate.
"""

import math
import json
import importlib.util
import os
import re
import random


# ─── Track Generation ───────────────────────────────────────────────────────

def generate_track(seed=42, num_points=12, scale=300, center=(400, 350)):
    """Generate a closed-loop track from control points."""
    rng = random.Random(seed)
    cx, cy = center
    points = []
    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        r = scale + rng.uniform(-80, 80)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    return points


def interpolate_track(control_points, resolution=500):
    """Catmull-Rom spline interpolation for smooth track."""
    n = len(control_points)
    track = []

    for i in range(n):
        p0 = control_points[(i - 1) % n]
        p1 = control_points[i]
        p2 = control_points[(i + 1) % n]
        p3 = control_points[(i + 2) % n]

        seg_points = resolution // n
        for j in range(seg_points):
            t = j / seg_points
            t2 = t * t
            t3 = t2 * t

            x = 0.5 * ((2 * p1[0]) +
                        (-p0[0] + p2[0]) * t +
                        (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                        (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) +
                        (-p0[1] + p2[1]) * t +
                        (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                        (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            track.append((x, y))

    return track


def compute_track_data(track_points):
    """Compute distances and curvatures for each track point."""
    n = len(track_points)
    distances = [0.0]
    curvatures = []

    for i in range(1, n):
        dx = track_points[i][0] - track_points[i - 1][0]
        dy = track_points[i][1] - track_points[i - 1][1]
        distances.append(distances[-1] + math.sqrt(dx * dx + dy * dy))

    for i in range(n):
        p0 = track_points[(i - 1) % n]
        p1 = track_points[i]
        p2 = track_points[(i + 1) % n]

        dx1 = p1[0] - p0[0]
        dy1 = p1[1] - p0[1]
        dx2 = p2[0] - p1[0]
        dy2 = p2[1] - p1[1]

        cross = abs(dx1 * dy2 - dy1 * dx2)
        d1 = math.sqrt(dx1 * dx1 + dy1 * dy1) + 0.001
        d2 = math.sqrt(dx2 * dx2 + dy2 * dy2) + 0.001
        curvatures.append(cross / (d1 * d2))

    total_length = distances[-1]
    # Add closing segment
    dx = track_points[0][0] - track_points[-1][0]
    dy = track_points[0][1] - track_points[-1][1]
    total_length += math.sqrt(dx * dx + dy * dy)

    return distances, curvatures, total_length


# ─── Car Loading ─────────────────────────────────────────────────────────────

STAT_BUDGET = 100
STAT_FIELDS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]
REQUIRED_FIELDS = ["CAR_NAME", "CAR_COLOR"] + STAT_FIELDS


def load_car(filepath):
    """Load and validate a car module."""
    name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    car = {}
    for field in REQUIRED_FIELDS:
        if not hasattr(mod, field):
            raise ValueError(f"{filepath}: missing {field}")
        car[field] = getattr(mod, field)

    # Validate hex color
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", car["CAR_COLOR"]):
        raise ValueError(f"{filepath}: CAR_COLOR must be a valid hex color (e.g. #FF0000), got '{car['CAR_COLOR']}'")

    # Validate stat types
    for field in STAT_FIELDS:
        val = car[field]
        if not isinstance(val, (int, float)):
            raise ValueError(f"{filepath}: {field} must be numeric, got {type(val).__name__}")
        if val < 0:
            raise ValueError(f"{filepath}: {field} must not be negative, got {val}")

    total = sum(car[s] for s in STAT_FIELDS)
    if total > STAT_BUDGET:
        raise ValueError(f"{car['CAR_NAME']}: budget {total} exceeds {STAT_BUDGET} (over by {total - STAT_BUDGET})")

    if hasattr(mod, "strategy"):
        car["strategy"] = mod.strategy
    else:
        car["strategy"] = lambda state: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}

    car["file"] = filepath
    return car


def load_all_cars(directory):
    """Load all car files from a directory."""
    cars = []
    for f in sorted(os.listdir(directory)):
        if f.endswith(".py") and not f.startswith("_"):
            try:
                car = load_car(os.path.join(directory, f))
                cars.append(car)
                print(f"  Loaded: {car['CAR_NAME']} ({f})")
            except Exception as e:
                print(f"  FAILED: {f} — {e}")
    return cars


# ─── Simulation ──────────────────────────────────────────────────────────────

class RaceSim:
    TICKS_PER_SEC = 30
    TRACK_WIDTH = 50

    def __init__(self, cars, track_points, laps=3, seed=42, track_name=None):
        self.cars = cars
        self.track = track_points
        self.laps = laps
        self.rng = random.Random(seed)
        self.track_name = track_name

        self.distances, self.curvatures, self.track_length = compute_track_data(track_points)
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

            # Boost activation
            if wants_boost and state["boost_available"] and state["boost_active"] == 0:
                state["boost_active"] = self.TICKS_PER_SEC * 3  # 3 seconds
                state["boost_available"] = False

            if state["boost_active"] > 0:
                state["boost_active"] -= 1

            # Physics
            power = state["power"]
            grip = state["grip"]
            weight = state["weight"]
            aero = state["aero"]
            brakes = state["brakes"]

            # Tire wear affects grip
            tire_grip_mult = max(0.3, 1.0 - state["tire_wear"] * 0.7)

            # Tire wear rate depends on mode
            wear_rates = {"conserve": 0.00008, "balanced": 0.00018, "push": 0.00035}
            wear_rate = wear_rates.get(tire_mode, 0.0001)
            state["tire_wear"] = min(1.0, state["tire_wear"] + wear_rate)

            # Max speed from power (lighter = faster)
            base_max_speed = 160 + power * 100 - weight * 25
            if state["boost_active"] > 0:
                base_max_speed *= 1.25

            # Curvature penalty — grip-based ceiling, not proportional to power
            curv = self.get_curvature_at(state["distance"])
            effective_grip = grip * tire_grip_mult
            # Corner speed is an absolute ceiling based on grip, not scaled to power
            grip_corner_ceiling = 100 + effective_grip * 200
            corner_penalty = curv * (4.0 - effective_grip * 3.0)
            corner_speed_limit = grip_corner_ceiling * max(0.2, 1.0 - corner_penalty)
            corner_speed_limit = max(35, corner_speed_limit)

            target_speed = min(base_max_speed, corner_speed_limit) * throttle

            # Acceleration / braking
            mass_factor = 1.0 + weight * 0.5
            accel_rate = (60 + power * 80) / mass_factor * dt
            brake_rate = (80 + brakes * 100) * dt

            if target_speed > state["speed"]:
                state["speed"] = min(target_speed, state["speed"] + accel_rate)
            else:
                state["speed"] = max(target_speed, state["speed"] - brake_rate)

            # Drafting bonus
            for other in self.states:
                if other["car_idx"] == state["car_idx"] or other["finished"]:
                    continue
                dist_ahead = other["distance"] - state["distance"]
                if 5 < dist_ahead < 40:
                    draft_bonus = aero * 8 * (1 - dist_ahead / 40)
                    state["speed"] += draft_bonus * dt

            # Speed can't go negative
            state["speed"] = max(0, state["speed"])

            # Update distance
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

        # Record frame
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
        self.tick += 1

        # Check if race is over
        if all(s["finished"] for s in self.states):
            self.race_over = True

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


# ─── Main Entry ──────────────────────────────────────────────────────────────

def run_race(car_dir="cars", laps=3, track_seed=42, output="replay.json"):
    """Load cars, run race, export replay."""
    print(f"\n🏁 NPC RACE — {laps} laps")
    print(f"{'─' * 40}")
    print(f"Loading cars from: {car_dir}/\n")

    cars = load_all_cars(car_dir)
    if len(cars) < 2:
        raise ValueError("Need at least 2 cars to race!")

    print(f"\n{len(cars)} cars on the grid")
    print(f"Track seed: {track_seed}")
    print(f"{'─' * 40}\n")

    # Generate track
    control = generate_track(seed=track_seed, num_points=12)
    track = interpolate_track(control, resolution=500)

    # Run sim
    sim = RaceSim(cars, track, laps=laps, seed=track_seed)
    results = sim.run()

    # Print results
    print("🏆 RESULTS")
    print(f"{'─' * 40}")
    for r in results:
        status = f"Tick {r['finish_tick']}" if r["finished"] else "DNF"
        print(f"  P{r['position']}  {r['name']:20s}  {status}")

    # Export replay
    replay = sim.export_replay()
    with open(output, "w") as f:
        json.dump(replay, f)
    print(f"\nReplay saved: {output}")
    print(f"Total frames: {len(replay['frames'])}")

    return results
