"""
SlipStream — The drafter.
High aero build. Sits behind others for draft bonus, then slingshots past.
"""

CAR_NAME = "SlipStream"
CAR_COLOR = "#00aaff"

POWER = 20
GRIP = 15
WEIGHT = 15
AERO = 35
BRAKES = 15


def strategy(state):
    behind_someone = any(
        0 < c["distance_ahead"] < 35 for c in state["nearby_cars"]
    )

    # Drafting — sit tight and conserve
    if behind_someone and state["position"] > 1:
        tire_mode = "conserve"
        throttle = 0.95  # just enough to stay in draft range
    else:
        tire_mode = "balanced"
        throttle = 1.0

    # Boost when close behind someone on last lap
    use_boost = (
        state["lap"] >= state["total_laps"] - 1
        and state["boost_available"]
        and behind_someone
    )

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": tire_mode,
    }
