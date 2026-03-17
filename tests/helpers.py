"""Shared test helpers for NPC Race car strategy tests."""

import importlib
import sys


CAR_MODULES = ["gooseloose", "silky", "glasscanon", "brickhouse", "slipstream"]

# Maps lowercase module name to proper CAR_NAME (capitalized)
CAR_NAME_MAP = {
    "brickhouse": "BrickHouse",
    "glasscanon": "GlassCanon",
    "gooseloose": "GooseLoose",
    "silky": "Silky",
    "slipstream": "SlipStream",
}


def _load_car(name: str):
    """Import a car module by name, reloading to reset module-level state."""
    mod_name = f"cars.{name}"
    if mod_name in sys.modules:
        return importlib.reload(sys.modules[mod_name])
    return importlib.import_module(mod_name)


def _make_state(**overrides) -> dict:
    """Build a minimal strategy state dict with sensible defaults."""
    base = {
        "speed": 180.0,
        "position": 3,
        "total_cars": 5,
        "lap": 5,
        "total_laps": 20,
        "tire_wear": 0.3,
        "boost_available": True,
        "boost_active": False,
        "curvature": 0.0,
        "nearby_cars": [],
        "distance": 5000.0,
        "track_length": 5000.0,
        "lateral": 0.0,
        "fuel_remaining": 50.0,
        "fuel_pct": 0.6,
        "tire_compound": "medium",
        "tire_age_laps": 5,
        "engine_mode": "standard",
        "pit_status": "racing",
        "pit_stops": 0,
        "gap_ahead_s": 1.5,
        "gap_behind_s": 2.0,
        "data_file": None,
        "race_number": 1,
        "track_name": None,
    }
    base.update(overrides)
    return base
