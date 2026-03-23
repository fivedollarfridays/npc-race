"""DriftKing -- Midfield grip monster. Late braker, tyre whisperer."""

CAR_NAME = "DriftKing"
CAR_COLOR = "#8e44ad"

POWER = 21
GRIP = 24
WEIGHT = 18
AERO = 20
BRAKES = 17


def strategy(state):
    """Midfield: balanced approach, 1-stop, position-aware modes."""
    decision = {}
    decision["engine_mode"] = "standard"
    gap = state.get("gap_ahead_s", 99)
    if gap < 2.0:
        decision["engine_mode"] = "push"
    decision["tire_mode"] = "balanced"
    if state.get("tire_wear", 0) > 0.80:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    return decision
