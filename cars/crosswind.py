"""CrossWind -- Midfield aero specialist. Punches above weight on fast tracks."""

CAR_NAME = "CrossWind"
CAR_COLOR = "#2980b9"

POWER = 23
GRIP = 19
WEIGHT = 18
AERO = 23
BRAKES = 17


def strategy(state):
    """Midfield: balanced approach, 1-stop, position-aware modes."""
    decision = {}
    decision["engine_mode"] = "standard"
    gap = state.get("gap_ahead_s", 99)
    if gap < 2.0:
        decision["engine_mode"] = "push"
    decision["tire_mode"] = "balanced"
    if state.get("tire_wear", 0) > 0.70:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    return decision
