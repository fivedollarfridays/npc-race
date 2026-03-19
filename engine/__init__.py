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
                      update_speed, compute_lateral_push, compute_aero_grip)
from .timing import (create_timing, update_timing, get_sector_boundaries,
                     get_fastest_lap, get_timing_summary, CarTiming)
from .dirty_air import compute_dirty_air_factor
from .collision import check_collisions, is_contact
from .damage import create_damage_state, apply_damage, compute_damage_penalties, repair_in_pit
from .incident import (compute_spin_risk, check_spin, create_spin_event,
                       compute_lockup_risk, create_lockup_event)
from .safety_car import (create_sc_state, trigger_sc, update_sc, get_sc_speed_limit,
                          get_sc_modifiers, is_sc_active, should_compress_gaps)
from .weather_model import (create_weather_state, update_weather, get_wetness_grip_mult,
                             get_wetness_wear_mult, generate_forecast, get_optimal_compound)
from .drama import process_collisions, update_step_systems, process_spin_risk
from .ers_model import create_ers_state, update_ers, get_ers_speed_bonus, reset_ers_lap
from .brake_model import create_brake_state, update_brake_temp, get_brake_efficiency
from .visibility import build_opponent_info, filter_nearby_cars, OBSERVABLE_FIELDS, PRIVATE_FIELDS
from .narrative import detect_events, RaceEvent
from .commentary import format_events, format_event, format_time
from .race_report import generate_report

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
    "compute_aero_grip",
    "create_timing",
    "update_timing",
    "get_sector_boundaries",
    "get_fastest_lap",
    "get_timing_summary",
    "CarTiming",
    "compute_dirty_air_factor",
    "check_collisions",
    "is_contact",
    "create_damage_state",
    "apply_damage",
    "compute_damage_penalties",
    "repair_in_pit",
    "compute_spin_risk",
    "check_spin",
    "create_spin_event",
    "compute_lockup_risk",
    "create_lockup_event",
    "create_sc_state",
    "trigger_sc",
    "update_sc",
    "get_sc_speed_limit",
    "get_sc_modifiers",
    "is_sc_active",
    "should_compress_gaps",
    "create_weather_state",
    "update_weather",
    "get_wetness_grip_mult",
    "get_wetness_wear_mult",
    "generate_forecast",
    "get_optimal_compound",
    "process_collisions",
    "update_step_systems",
    "process_spin_risk",
    "create_ers_state", "update_ers", "get_ers_speed_bonus", "reset_ers_lap",
    "create_brake_state", "update_brake_temp", "get_brake_efficiency",
    "build_opponent_info", "filter_nearby_cars", "OBSERVABLE_FIELDS", "PRIVATE_FIELDS",
    "detect_events", "RaceEvent", "format_events", "format_event", "format_time",
    "generate_report",
]
