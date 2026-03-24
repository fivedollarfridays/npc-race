"""Berserker -- Wildcard rival. Always attack, always push, boost ASAP."""

CAR_NAME = "Berserker"
CAR_COLOR = "#e74c3c"

POWER = 30
GRIP = 22
WEIGHT = 16
AERO = 15
BRAKES = 17


def strategy(state):
    decision = {}
    decision["engine_mode"] = "push"
    decision["tire_mode"] = "push"
    decision["boost"] = True  # Use boost immediately
    if state.get("tire_wear", 0) > 0.55:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "soft"  # Always soft for speed
    return decision
