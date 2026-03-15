"""
BrickHouse — The brute.
Raw power and weight. Slow in corners, untouchable on straights.
"""

CAR_NAME = "BrickHouse"
CAR_COLOR = "#cc2222"

POWER = 35
GRIP = 10
WEIGHT = 25
AERO = 15
BRAKES = 15


def strategy(state):
    in_curve = state["curvature"] > 0.1

    # Heavy car — must brake early for corners
    if in_curve:
        throttle = 0.5
        tire_mode = "conserve"
    else:
        throttle = 1.0
        tire_mode = "push"

    # Boost on any straight when behind
    use_boost = (
        state["boost_available"]
        and not in_curve
        and state["position"] > 2
        and state["lap"] >= state["total_laps"] - 1
    )

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": tire_mode,
    }
