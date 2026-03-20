"""
Car loading and validation for NPC Race.

Loads car modules from .py files, validates stat budgets,
hex colors, and stat types/ranges.
"""

import importlib.util
import os
import re
from pathlib import Path

from .setup_model import validate_setup, apply_setup
from .parts_catalog import CATALOG, DEFAULTS, validate_build
from .car_attributes import compute_attributes

COMPONENT_CATEGORIES = list(CATALOG.keys())

try:
    from security.bot_scanner import scan_car_source as _scan_car_source
except ImportError:
    _scan_car_source = None


STAT_BUDGET = 100
STAT_FIELDS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]
REQUIRED_FIELDS = ["CAR_NAME", "CAR_COLOR"] + STAT_FIELDS


def _validate_car_fields(car, filepath):
    """Validate hex color, stat types, and budget for a loaded car dict."""
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", car["CAR_COLOR"]):
        raise ValueError(
            f"{filepath}: CAR_COLOR must be a valid hex color "
            f"(e.g. #FF0000), got '{car['CAR_COLOR']}'"
        )
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


def _is_component_car(mod) -> bool:
    """Check if car uses the component system (ENGINE is a string component ID)."""
    return hasattr(mod, "ENGINE") and isinstance(getattr(mod, "ENGINE"), str)


def _load_component_selections(mod) -> dict:
    """Extract component selections from a car module."""
    selections = {}
    for cat in COMPONENT_CATEGORIES:
        val = getattr(mod, cat, None)
        if isinstance(val, str):
            selections[cat] = val
        else:
            selections[cat] = DEFAULTS[cat]
    return selections


def _legacy_to_components(mod) -> dict:
    """Map legacy 5-stat car to component selections."""
    power = getattr(mod, "POWER", 20)
    grip = getattr(mod, "GRIP", 20)
    aero = getattr(mod, "AERO", 20)
    brakes = getattr(mod, "BRAKES", 20)
    weight = getattr(mod, "WEIGHT", 20)
    sel = dict(DEFAULTS)
    if power >= 28:
        sel["ENGINE"] = "pu_aggressive"
    elif power >= 23:
        sel["ENGINE"] = "pu_high_output"
    elif power <= 15:
        sel["ENGINE"] = "pu_efficient"
    if aero >= 30:
        sel["AERO"] = "aero_ground_effect"
    elif aero >= 22:
        sel["AERO"] = "aero_high_df"
    elif aero <= 12:
        sel["AERO"] = "aero_low_drag"
    if grip >= 25:
        sel["SUSPENSION"] = "sus_soft"
    elif grip <= 12:
        sel["SUSPENSION"] = "sus_stiff"
    if brakes >= 25:
        sel["BRAKES"] = "brk_aggressive"
    elif brakes <= 12:
        sel["BRAKES"] = "brk_endurance"
    if weight <= 12:
        sel["WEIGHT"] = "wt_stage2"
    elif weight <= 16:
        sel["WEIGHT"] = "wt_stage1"
    return sel


def load_car(filepath):
    """Load and validate a car module."""
    name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)

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

    _validate_car_fields(car, filepath)

    if hasattr(mod, "strategy"):
        car["strategy"] = mod.strategy
    else:
        car["strategy"] = lambda state: {
            "throttle": 1.0, "boost": False, "tire_mode": "balanced",
        }

    raw_setup = getattr(mod, "SETUP", {})
    car["setup_raw"] = validate_setup(raw_setup)
    car["stats"] = {k.lower(): car[k] for k in STAT_FIELDS}
    car["setup"] = apply_setup(car["stats"], car["setup_raw"])

    # Component system: derive performance attributes
    if _is_component_car(mod):
        selections = _load_component_selections(mod)
        valid, msg = validate_build(selections)
        if not valid:
            raise ValueError(f"{filepath}: {msg}")
        car["components"] = selections
    else:
        car["components"] = _legacy_to_components(mod)
    car["derived"] = compute_attributes(car["components"])

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
