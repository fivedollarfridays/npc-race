"""
GlassCanon — Yolo speed.
0-stop gamble on hards. Full push engine all race.
Blocks on straights when car behind is close. Full throttle everywhere.
"""

CAR_NAME = "GlassCanon"
CAR_COLOR = "#ffcc00"

POWER = 40
GRIP = 15
WEIGHT = 10
AERO = 20
BRAKES = 15


def strategy(state):
    nearby = state["nearby_cars"]
    curv = state["curvature"]

    # --- Pit strategy: 0-stop, never pit ---
    # --- Engine mode: full push always ---
    engine_mode = "push"

    # --- Throttle: full send, slight lift in tight corners ---
    in_curve = curv > 0.08
    throttle = 0.5 if in_curve else 1.0

    # --- Lateral: block on straights when car behind is close ---
    lateral = 0.0
    behind = [c for c in nearby if c["distance_ahead"] < 0]
    if not in_curve and behind and state["gap_behind_s"] < 1.0:
        closest = max(behind, key=lambda c: c["distance_ahead"])
        lateral = closest["lateral"]

    # --- Boost on first straight of last lap ---
    use_boost = (
        state["boost_available"]
        and state["lap"] >= state["total_laps"] - 1
        and not in_curve
    )

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": "push",
        "lateral_target": lateral,
        "pit_request": False,
        "tire_compound_request": None,
        "engine_mode": engine_mode,
    }
