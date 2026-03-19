"""Safety car state machine."""
import random

SC_PACE = 120.0
SC_MIN_LAPS = 3
SC_MAX_LAPS = 5
SC_GAP_TARGET = 1.0
SC_TIRE_DEG_MULT = 0.25
SC_FUEL_MULT = 0.25
SC_PIT_TIME_REDUCTION = 240  # ticks (~8s saved)

INACTIVE = "inactive"
DEPLOYED = "deployed"
ACTIVE = "active"
ENDING = "ending"


def create_sc_state() -> dict:
    """Return a fresh safety car state dict."""
    return {
        "status": INACTIVE,
        "laps_remaining": 0,
        "laps_active": 0,
        "reason": None,
        "deploy_tick": None,
        "deploy_lap": None,
    }


def trigger_sc(
    sc_state: dict, reason: str, rng: random.Random, tick: int, lap: int
) -> dict:
    """Deploy safety car. No-op if already active."""
    if sc_state["status"] != INACTIVE:
        return sc_state
    duration = rng.randint(SC_MIN_LAPS, SC_MAX_LAPS)
    return {
        "status": DEPLOYED,
        "laps_remaining": duration,
        "laps_active": 0,
        "reason": reason,
        "deploy_tick": tick,
        "deploy_lap": lap,
    }


def update_sc(sc_state: dict, leader_lap: int) -> dict:
    """Advance SC state machine based on leader's lap count.

    DEPLOYED -> ACTIVE after 1 lap.
    ACTIVE -> ENDING when laps_remaining reaches 1.
    ENDING -> INACTIVE when laps_remaining reaches 0.
    """
    st = sc_state.copy()
    if st["status"] == INACTIVE:
        return st

    if st["status"] == DEPLOYED:
        st["status"] = ACTIVE
        return st

    if st["status"] == ACTIVE:
        st["laps_remaining"] = max(0, st["laps_remaining"] - 1)
        st["laps_active"] += 1
        if st["laps_remaining"] <= 1:
            st["status"] = ENDING
        return st

    if st["status"] == ENDING:
        st["laps_remaining"] = max(0, st["laps_remaining"] - 1)
        if st["laps_remaining"] == 0:
            st["status"] = INACTIVE
            st["reason"] = None
        return st

    return st


def get_sc_speed_limit(sc_state: dict) -> float | None:
    """Return speed limit under SC, or None if inactive."""
    if sc_state["status"] in (DEPLOYED, ACTIVE, ENDING):
        return SC_PACE
    return None


def get_sc_modifiers(sc_state: dict) -> dict:
    """Return tire/fuel/pit modifiers during SC."""
    if sc_state["status"] in (DEPLOYED, ACTIVE, ENDING):
        return {
            "tire_deg_mult": SC_TIRE_DEG_MULT,
            "fuel_mult": SC_FUEL_MULT,
            "pit_time_reduction": SC_PIT_TIME_REDUCTION,
        }
    return {
        "tire_deg_mult": 1.0,
        "fuel_mult": 1.0,
        "pit_time_reduction": 0,
    }


def is_sc_active(sc_state: dict) -> bool:
    """True if SC is deployed, active, or ending."""
    return sc_state["status"] != INACTIVE


def should_compress_gaps(sc_state: dict) -> bool:
    """True if gaps should be compressed toward SC_GAP_TARGET."""
    return sc_state["status"] in (ACTIVE, ENDING)
