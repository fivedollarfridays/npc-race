"""Phantom -- frontrunner rival. Raw power, early pit threshold.

Generated from frontrunner archetype, seed=103.
"""

CAR_NAME = "Phantom"
CAR_COLOR = "#2c3e50"

POWER = 40
GRIP = 18
WEIGHT = 11
AERO = 15
BRAKES = 16


def strategy(state):
    """Frontrunner: push engine when behind, aggressive tire management."""
    decision = {}
    position = state.get("position", 1)
    decision["engine_mode"] = "push" if position > 1 else "standard"
    decision["tire_mode"] = "push"
    if state.get("tire_wear", 0) > 0.58:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    total_laps = state.get("total_laps", 5)
    final_laps = state.get("lap", 0) >= total_laps - 2
    decision["boost"] = state.get("boost_available", False) and final_laps
    return decision
