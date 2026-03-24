"""Tortoise -- Backmarker: conservative, survive the race, no heroics."""

CAR_NAME = "Tortoise"
CAR_COLOR = "#27ae60"

POWER = 15
GRIP = 18
WEIGHT = 26
AERO = 21
BRAKES = 20


def strategy(state):
    """Backmarker: conservative, survive the race, no heroics."""
    decision = {}
    decision["engine_mode"] = "conserve"
    decision["tire_mode"] = "conserve"
    if state.get("tire_wear", 0) > 0.80:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    decision["boost"] = False
    return decision
