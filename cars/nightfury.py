"""NightFury -- frontrunner rival. High power, aggressive strategy.

Generated from frontrunner archetype, seed=101.
"""

CAR_NAME = "NightFury"
CAR_COLOR = "#1a1a2e"

POWER = 35
GRIP = 17
WEIGHT = 19
AERO = 18
BRAKES = 11


def strategy(state):
    """Frontrunner: push engine when behind, aggressive tire management."""
    decision = {}
    position = state.get("position", 1)
    decision["engine_mode"] = "push" if position > 1 else "standard"
    decision["tire_mode"] = "push"
    if state.get("tire_wear", 0) > 0.61:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    total_laps = state.get("total_laps", 5)
    final_laps = state.get("lap", 0) >= total_laps - 2
    decision["boost"] = state.get("boost_available", False) and final_laps
    return decision
