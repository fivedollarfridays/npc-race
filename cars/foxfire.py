"""FoxFire -- Midfield agility car. Quick on brakes, nimble in corners."""

CAR_NAME = "FoxFire"
CAR_COLOR = "#e67e22"

POWER = 24
GRIP = 24
WEIGHT = 15
AERO = 18
BRAKES = 19


def strategy(state):
    """Midfield: balanced approach, 1-stop, position-aware modes."""
    decision = {}
    decision["engine_mode"] = "standard"
    gap = state.get("gap_ahead_s", 99)
    if gap < 2.0:
        decision["engine_mode"] = "push"
    decision["tire_mode"] = "balanced"
    if state.get("tire_wear", 0) > 0.75:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    return decision
