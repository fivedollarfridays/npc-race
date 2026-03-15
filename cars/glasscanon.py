"""
GlassCanon — Yolo speed.
Almost everything in power. Pray for straights.
"""

CAR_NAME = "GlassCanon"
CAR_COLOR = "#ffcc00"

POWER = 40
GRIP = 15
WEIGHT = 10
AERO = 20
BRAKES = 15


def strategy(state):
    in_curve = state["curvature"] > 0.08

    # Must manage corners carefully with low grip
    if in_curve:
        throttle = 0.4
    else:
        throttle = 1.0

    # Always push tires — we win on speed or we lose
    tire_mode = "push"

    # Boost immediately on first straight of last lap
    use_boost = (
        state["boost_available"]
        and state["lap"] >= state["total_laps"] - 1
        and not in_curve
    )

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": tire_mode,
    }
