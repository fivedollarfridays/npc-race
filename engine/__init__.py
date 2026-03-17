"""
NPC Race Engine — hub module.

Re-exports the public API so that ``from engine import run_race``
continues to work after the monolith was split into focused modules.
"""

from tracks import get_track, list_tracks, random_track
from .track_gen import generate_track, interpolate_track, compute_track_data
from .car_loader import load_car, load_all_cars, STAT_BUDGET, STAT_FIELDS, REQUIRED_FIELDS
from .simulation import RaceSim
from .race_runner import run_race
from .tire_model import get_compound, compute_grip_multiplier, get_compound_names
from .fuel_model import get_engine_mode, get_engine_mode_names
from .pit_lane import create_pit_state, is_in_pit

__all__ = [
    "get_track",
    "list_tracks",
    "random_track",
    "generate_track",
    "interpolate_track",
    "compute_track_data",
    "load_car",
    "load_all_cars",
    "STAT_BUDGET",
    "STAT_FIELDS",
    "REQUIRED_FIELDS",
    "RaceSim",
    "run_race",
    "get_compound",
    "compute_grip_multiplier",
    "get_compound_names",
    "get_engine_mode",
    "get_engine_mode_names",
    "create_pit_state",
    "is_in_pit",
]
