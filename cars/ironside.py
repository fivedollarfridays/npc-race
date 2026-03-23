"""IronSide -- Midfield tank. Balanced stats, sturdy in traffic."""

CAR_NAME = "IronSide"
CAR_COLOR = "#7f8c8d"

POWER = 22
GRIP = 22
WEIGHT = 19
AERO = 19
BRAKES = 18


def strategy(state):
    """Midfield: balanced approach, 1-stop, position-aware modes."""
    decision = {}
    decision["engine_mode"] = "standard"
    gap = state.get("gap_ahead_s", 99)
    if gap < 2.0:
        decision["engine_mode"] = "push"
    decision["tire_mode"] = "balanced"
    if state.get("tire_wear", 0) > 0.65:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    return decision
