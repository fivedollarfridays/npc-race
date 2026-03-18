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
from .tire_temperature import heat_generation, heat_dissipation, update_tire_temp, tire_temp_grip_factor
from .drs_system import get_drs_zones, is_in_drs_zone, drs_speed_multiplier, update_drs_state
from .setup_model import validate_setup, apply_setup, DEFAULT_SETUP
from .physics import (compute_target_speed, compute_acceleration,
                      compute_braking, compute_draft_bonus, compute_mass_factor,
                      update_speed, compute_lateral_push)
from .timing import (create_timing, update_timing, get_sector_boundaries,
                     get_fastest_lap, get_timing_summary, CarTiming)

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
    "heat_generation",
    "heat_dissipation",
    "update_tire_temp",
    "tire_temp_grip_factor",
    "get_drs_zones",
    "is_in_drs_zone",
    "drs_speed_multiplier",
    "update_drs_state",
    "validate_setup",
    "apply_setup",
    "DEFAULT_SETUP",
    "compute_target_speed",
    "compute_acceleration",
    "compute_braking",
    "compute_draft_bonus",
    "compute_mass_factor",
    "update_speed",
    "compute_lateral_push",
    "create_timing",
    "update_timing",
    "get_sector_boundaries",
    "get_fastest_lap",
    "get_timing_summary",
    "CarTiming",
]
