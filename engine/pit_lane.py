"""Pit lane state machine for pit stop simulation.

State machine: racing -> pit_entry -> pit_stationary -> pit_exit -> racing
"""

PIT_SPEED_LIMIT = 80.0    # km/h speed limit in pit lane
PIT_ENTRY_TICKS = 60      # ~2 seconds to enter pit (at 30 tps)
PIT_STOP_TICKS = 660      # ~22 seconds stationary for tire change
PIT_EXIT_TICKS = 60       # ~2 seconds to exit pit


def request_pit_stop(pit_state: dict, compound_name: str) -> dict:
    """Queue a pit stop. Only works when status is 'racing'.

    Returns updated pit_state (does not mutate input).
    """
    result = dict(pit_state)
    if result["status"] == "racing":
        result["pending_request"] = True
        result["requested_compound"] = compound_name
    return result


def update_pit_state(pit_state: dict) -> tuple[dict, bool]:
    """Tick the pit state machine forward by one step.

    Returns (updated_pit_state, completed) where completed=True only on
    the tick when pit_exit transitions back to racing.
    """
    result = dict(pit_state)
    completed = False

    if result["status"] == "racing" and result["pending_request"]:
        result["status"] = "pit_entry"
        result["pit_timer"] = PIT_ENTRY_TICKS
        result["pending_request"] = False
    elif result["status"] == "pit_entry":
        result["pit_timer"] -= 1
        if result["pit_timer"] <= 0:
            result["status"] = "pit_stationary"
            result["pit_timer"] = PIT_STOP_TICKS
    elif result["status"] == "pit_stationary":
        result["pit_timer"] -= 1
        if result["pit_timer"] <= 0:
            result["status"] = "pit_exit"
            result["pit_timer"] = PIT_EXIT_TICKS
    elif result["status"] == "pit_exit":
        result["pit_timer"] -= 1
        if result["pit_timer"] <= 0:
            result["status"] = "racing"
            completed = True

    return result, completed


def is_in_pit(pit_state: dict) -> bool:
    """Return True if the car is in any pit phase (not racing)."""
    return pit_state["status"] != "racing"


def get_speed_limit(pit_state: dict) -> float | None:
    """Return PIT_SPEED_LIMIT during pit_entry or pit_exit, None otherwise."""
    if pit_state["status"] in ("pit_entry", "pit_exit"):
        return PIT_SPEED_LIMIT
    return None


def complete_pit_stop(pit_state: dict) -> tuple[dict, str]:
    """Finalize a pit stop: increment counter, return new compound.

    Called when pit_exit finishes. Returns (updated_state, compound_name).
    Does not mutate input.
    """
    result = dict(pit_state)
    compound = result["requested_compound"]
    result["pit_stops"] += 1
    result["requested_compound"] = None
    return result, compound


def create_pit_state() -> dict:
    """Return a fresh pit state dict with default values."""
    return {
        "status": "racing",
        "pit_timer": 0,
        "pit_stops": 0,
        "requested_compound": None,
        "pending_request": False,
    }
