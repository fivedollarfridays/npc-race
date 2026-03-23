"""SteamRoller -- Backmarker: conservative, survive the race, no heroics."""

CAR_NAME = "SteamRoller"
CAR_COLOR = "#c0392b"

POWER = 20
GRIP = 16
WEIGHT = 28
AERO = 17
BRAKES = 19


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
