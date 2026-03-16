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
]
