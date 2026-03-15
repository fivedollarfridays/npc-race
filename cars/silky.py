"""
Silky — The corner carver.
High grip, low power. Makes up time where others brake.
"""

CAR_NAME = "Silky"
CAR_COLOR = "#aa44ff"

POWER = 15
GRIP = 35
WEIGHT = 15
AERO = 15
BRAKES = 20


def strategy(state):
    # High grip means we can stay on throttle through corners
    throttle = 1.0 if state["curvature"] < 0.3 else 0.85

    # Conserve tires early, push when others are worn
    if state["lap"] < state["total_laps"] // 2:
        tire_mode = "conserve"
    else:
        tire_mode = "push"

    # Boost in tight section where others slow down
    use_boost = (
        state["boost_available"]
        and state["curvature"] > 0.1
        and state["lap"] >= state["total_laps"] - 1
    )

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": tire_mode,
    }
