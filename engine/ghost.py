"""Ghost car system -- adversarial teaching through calibrated flaws."""

from __future__ import annotations

from engine.parts_api import get_defaults

GHOST_LEVELS: dict[int, dict] = {
    1: {
        "name": "Ghost",
        "color": "#555555",
        "flaw": "gearbox",
        "description": "Over-revving engine (shifts at 14,000 RPM)",
        "laps": 1,
        "gearbox_shift_rpm": 14000,
        "cooling_effort": 0.48,
        "pit_threshold": 0.7,
    },
    2: {
        "name": "Ghost",
        "color": "#555555",
        "flaw": "gearbox",
        "description": "Shifting past peak torque (12,800 RPM)",
        "laps": 1,
        "gearbox_shift_rpm": 12800,
        "cooling_effort": 0.48,
        "pit_threshold": 0.7,
    },
    3: {
        "name": "Ghost",
        "color": "#555555",
        "flaw": "cooling",
        "description": "Overcooling -- maximum drag (effort 1.0)",
        "laps": 1,
        "gearbox_shift_rpm": 11000,
        "cooling_effort": 1.0,
        "pit_threshold": 0.7,
    },
    4: {
        "name": "Ghost",
        "color": "#555555",
        "flaw": "strategy",
        "description": "Never pits -- tires degrade with no recovery",
        "laps": 3,
        "gearbox_shift_rpm": 11000,
        "cooling_effort": 0.3,
        "pit_threshold": 999.0,
    },
    5: {
        "name": "Tortoise",
        "color": "#27ae60",
        "flaw": None,
        "description": "Weakest rival -- beat it to join the grid",
        "laps": 1,
        "use_rival": "tortoise",
    },
}


def create_ghost(level: int) -> dict:
    """Create a ghost car dict for PartsRaceSim.

    Returns a car dict with CAR_NAME, CAR_COLOR, stats, parts,
    and hardware specs.
    """
    if level not in GHOST_LEVELS:
        raise ValueError(f"Invalid ghost level: {level}. Use 1-5.")

    config = GHOST_LEVELS[level]

    if config.get("use_rival"):
        return _load_rival(config["use_rival"], config)

    return _build_ghost(config)


def _build_ghost(config: dict) -> dict:
    """Build a ghost car with calibrated part functions."""
    defaults = get_defaults()
    shift_rpm = config["gearbox_shift_rpm"]
    cool_effort = config["cooling_effort"]
    pit_threshold = config["pit_threshold"]

    def ghost_gearbox(rpm, speed, current_gear, throttle):
        if rpm > shift_rpm and current_gear < 8:
            return current_gear + 1
        if rpm < 5500 and current_gear > 1:
            return current_gear - 1
        return current_gear

    def ghost_cooling(engine_temp, brake_temp, battery_temp, speed):
        return cool_effort

    def ghost_strategy(state):
        decision = {}
        if state.get("tire_wear", 0) > pit_threshold:
            decision["pit_request"] = True
            decision["tire_compound_request"] = "hard"
        return decision

    parts = dict(defaults)
    parts["gearbox"] = ghost_gearbox
    parts["cooling"] = ghost_cooling
    parts["strategy"] = ghost_strategy

    return {
        "CAR_NAME": config["name"],
        "CAR_COLOR": config["color"],
        "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
        "parts": parts,
        "engine_spec": "v6_1000hp",
        "aero_spec": "medium_downforce",
        "chassis_spec": "standard",
        "_source": "",
    }


def _load_rival(rival_name: str, config: dict) -> dict:
    """Load an actual rival car file."""
    import os
    from engine.car_loader import load_car

    cars_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "cars",
    )
    car_path = os.path.join(cars_dir, f"{rival_name}.py")

    if not os.path.isfile(car_path):
        raise FileNotFoundError(f"Rival car not found: {car_path}")

    car = load_car(car_path)
    car["CAR_COLOR"] = config.get("color", car["CAR_COLOR"])
    return car
