"""DRS (Drag Reduction System) — models F1 drag reduction on straights.

DRS reduces drag on designated zones when a car is within 1 second
of the car ahead.  Each zone is a (start_pct, end_pct) tuple
representing a fraction 0.0-1.0 of total lap distance.
"""

DRS_GAP_THRESHOLD: float = 1.0  # seconds


def get_drs_zones(track_dict: dict) -> list[tuple[float, float]]:
    """Return the track's DRS zones, defaulting to [] if none defined."""
    return track_dict.get("drs_zones", [])


def is_in_drs_zone(distance_pct: float, zones: list[tuple[float, float]]) -> bool:
    """True if *distance_pct* falls inside any (start_pct, end_pct) zone."""
    for start, end in zones:
        if start <= distance_pct <= end:
            return True
    return False


def drs_speed_multiplier(in_zone: bool, drs_active: bool) -> float:
    """Return 1.05 when both *in_zone* and *drs_active*, else 1.0."""
    if in_zone and drs_active:
        return 1.05
    return 1.0


def update_drs_state(
    drs_available: bool,
    drs_active: bool,
    drs_requested: bool,
    in_zone: bool,
    gap_ahead_s: float,
    lap_changed: bool,
) -> tuple[bool, bool]:
    """Return (new_drs_available, new_drs_active).

    Rules:
    - lap_changed  -> reset: available=True, active=False
    - Activate if  -> requested AND in_zone AND gap<=threshold AND available
                      then available=False, active=True  (used for this lap)
    - Deactivate   -> if NOT in_zone: active=False  (available stays as-is)
    - Otherwise    -> carry forward current state
    """
    if lap_changed:
        return True, False

    if (
        drs_requested
        and in_zone
        and gap_ahead_s <= DRS_GAP_THRESHOLD
        and drs_available
    ):
        return False, True

    if not in_zone:
        return drs_available, False

    return drs_available, drs_active
