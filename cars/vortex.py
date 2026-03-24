"""Vortex -- frontrunner rival. High aero, calculated aggression.

Generated from frontrunner archetype, seed=102.
"""

CAR_NAME = "Vortex"
CAR_COLOR = "#6c3483"

POWER = 35
GRIP = 19
WEIGHT = 13
AERO = 21
BRAKES = 12


def strategy(state):
    """Frontrunner: push engine when behind, aggressive tire management."""
    decision = {}
    position = state.get("position", 1)
    decision["engine_mode"] = "push" if position > 1 else "standard"
    decision["tire_mode"] = "push"
    if state.get("tire_wear", 0) > 0.69:
        decision["pit_request"] = True
        decision["tire_compound_request"] = "hard"
    total_laps = state.get("total_laps", 5)
    final_laps = state.get("lap", 0) >= total_laps - 2
    decision["boost"] = state.get("boost_available", False) and final_laps
    return decision
