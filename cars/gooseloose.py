"""
GooseLoose — The founder car.
Balanced build with aggressive tire strategy. Pushes hard early, conserves late.
"""

CAR_NAME = "GooseLoose"
CAR_COLOR = "#ff6600"

POWER = 25
GRIP = 25
WEIGHT = 15
AERO = 20
BRAKES = 15


def strategy(state):
    lap_pct = state["lap"] / max(state["total_laps"], 1)
    in_corners = state["curvature"] > 0.15

    # Push tires early, conserve for last third
    if lap_pct < 0.6:
        tire_mode = "push"
    elif state["tire_wear"] > 0.6:
        tire_mode = "conserve"
    else:
        tire_mode = "balanced"

    # Throttle management in corners
    if in_corners and state["speed"] > 160:
        throttle = 0.7
    else:
        throttle = 1.0

    # Boost on last lap if not in first
    use_boost = (
        state["lap"] >= state["total_laps"] - 1
        and state["boost_available"]
        and state["position"] > 1
    )

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": tire_mode,
    }
