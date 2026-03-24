"""PaperWeight -- Backmarker: conservative, survive the race, no heroics."""

CAR_NAME = "PaperWeight"
CAR_COLOR = "#95a5a6"

POWER = 22
GRIP = 13
WEIGHT = 25
AERO = 23
BRAKES = 17


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
