"""Chameleon -- Wildcard rival. Mirrors behavior based on position."""

CAR_NAME = "Chameleon"
CAR_COLOR = "#1abc9c"

POWER = 34
GRIP = 20
WEIGHT = 14
AERO = 21
BRAKES = 11


def strategy(state):
    decision = {}
    pos = state.get("position", 10)
    # Mirror: aggressive when behind, defensive when ahead
    if pos > 10:
        decision["engine_mode"] = "push"
        decision["tire_mode"] = "push"
    elif pos <= 3:
        decision["engine_mode"] = "conserve"
        decision["tire_mode"] = "conserve"
    else:
        decision["engine_mode"] = "standard"
        decision["tire_mode"] = "balanced"
    if state.get("tire_wear", 0) > 0.70:
        decision["pit_request"] = True
    return decision
