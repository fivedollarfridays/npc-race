"""
BrickHouse — The brute.
2-stop: soft -> medium -> hard. Push engine early, conserve late.
Wide lateral stance. Heavy car needs fresh tires to compete.
"""

CAR_NAME = "BrickHouse"
CAR_COLOR = "#cc2222"

POWER = 35
GRIP = 10
WEIGHT = 25
AERO = 15
BRAKES = 15


def strategy(state):
    lap = state["lap"]
    total = max(state["total_laps"], 1)
    lap_pct = lap / total
    pit_stops = state["pit_stops"]
    curv = state["curvature"]

    # --- Pit strategy: 2-stop at ~30% and ~65% ---
    pit_request = False
    compound_req = None
    if pit_stops == 0 and lap_pct >= 0.25:
        pit_request = True
        compound_req = "medium"
    elif pit_stops == 1 and lap_pct >= 0.60:
        pit_request = True
        compound_req = "hard"

    # --- Engine mode: push early, conserve in final stint ---
    if pit_stops < 2:
        engine_mode = "push"
    else:
        engine_mode = "conserve"

    # --- Throttle: heavy car brakes early for corners ---
    in_curve = curv > 0.1
    throttle = 0.5 if in_curve else 1.0

    # --- Lateral: wide stance, varies position for intimidation ---
    lateral = 0.6 if (lap % 2 == 0) else -0.6

    # --- Boost on straight when behind ---
    use_boost = (
        state["boost_available"]
        and not in_curve
        and state["position"] > 2
        and lap >= total - 1
    )

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": "balanced",
        "lateral_target": lateral,
        "pit_request": pit_request,
        "tire_compound_request": compound_req,
        "engine_mode": engine_mode,
    }
