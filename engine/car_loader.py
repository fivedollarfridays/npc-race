"""
Car loading and validation for NPC Race.

Loads car modules from .py files, validates stat budgets,
hex colors, and stat types/ranges.
"""

import importlib.util
import os
import re
from pathlib import Path

try:
    from security.bot_scanner import scan_car_source as _scan_car_source
except ImportError:
    _scan_car_source = None


STAT_BUDGET = 100
STAT_FIELDS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]
REQUIRED_FIELDS = ["CAR_NAME", "CAR_COLOR"] + STAT_FIELDS


def load_car(filepath):
    """Load and validate a car module."""
    name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)

    # Security scan before executing untrusted code
    if _scan_car_source is not None:
        source = Path(filepath).read_text(encoding="utf-8")
        scan_result = _scan_car_source(source)
        if not scan_result.passed:
            raise ValueError(
                f"Car file {filepath} failed security scan: "
                f"{scan_result.violations}"
            )

    spec.loader.exec_module(mod)

    car = {}
    for field in REQUIRED_FIELDS:
        if not hasattr(mod, field):
            raise ValueError(f"{filepath}: missing {field}")
        car[field] = getattr(mod, field)

    # Validate hex color
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", car["CAR_COLOR"]):
        raise ValueError(
            f"{filepath}: CAR_COLOR must be a valid hex color "
            f"(e.g. #FF0000), got '{car['CAR_COLOR']}'"
        )

    # Validate stat types
    for field in STAT_FIELDS:
        val = car[field]
        if not isinstance(val, (int, float)):
            raise ValueError(
                f"{filepath}: {field} must be numeric, got {type(val).__name__}"
            )
        if val < 0:
            raise ValueError(
                f"{filepath}: {field} must not be negative, got {val}"
            )

    total = sum(car[s] for s in STAT_FIELDS)
    if total > STAT_BUDGET:
        raise ValueError(
            f"{car['CAR_NAME']}: budget {total} exceeds "
            f"{STAT_BUDGET} (over by {total - STAT_BUDGET})"
        )

    if hasattr(mod, "strategy"):
        car["strategy"] = mod.strategy
    else:
        car["strategy"] = lambda state: {
            "throttle": 1.0, "boost": False, "tire_mode": "balanced",
        }

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
                print(f"  FAILED: {f} -- {e}")
    return cars
