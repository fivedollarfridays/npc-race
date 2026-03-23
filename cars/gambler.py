"""Gambler -- Wildcard rival. Random-ish pit timing based on lap modulo."""

CAR_NAME = "Gambler"
CAR_COLOR = "#f1c40f"

POWER = 29
GRIP = 21
WEIGHT = 18
AERO = 18
BRAKES = 14


def strategy(state):
    decision = {}
    lap = state.get("lap", 0)
    decision["engine_mode"] = "push" if lap % 3 == 0 else "standard"
    decision["tire_mode"] = "push" if state.get("position", 10) > 5 else "balanced"
    if lap > 0 and lap % 15 == 0:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "medium"
    decision["boost"] = state.get("position", 10) <= 3
    return decision
