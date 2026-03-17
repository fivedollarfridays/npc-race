"""
GooseLoose — The founder car.
1-stop: medium -> hard. Push engine first stint, standard second.
Defends position with lateral blocking. Backs off in tight corners.
"""

CAR_NAME = "GooseLoose"
CAR_COLOR = "#ff6600"

POWER = 25
GRIP = 25
WEIGHT = 15
AERO = 20
BRAKES = 15


def strategy(state):
    lap = state["lap"]
    total = max(state["total_laps"], 1)
    lap_pct = lap / total
    pit_stops = state["pit_stops"]

    # --- Pit strategy: 1-stop at ~45% ---
    pit_request = False
    compound_req = None
    if pit_stops == 0 and lap_pct >= 0.40:
        pit_request = True
        compound_req = "hard"

    # --- Engine mode: push first stint, standard after pit ---
    engine_mode = "push" if pit_stops == 0 else "standard"

    # --- Throttle: back off in tight corners ---
    in_corner = state["curvature"] > 0.15
    throttle = 0.7 if in_corner and state["speed"] > 160 else 1.0

    # --- Lateral: block when car behind is close ---
    lateral = 0.0
    nearby = state["nearby_cars"]
    behind = [c for c in nearby if c["distance_ahead"] < 0]
    if behind and state["gap_behind_s"] < 1.0:
        # Mirror the closest car behind to block
        closest = max(behind, key=lambda c: c["distance_ahead"])
        lateral = closest["lateral"]

    # --- Boost on last lap if not leading ---
    use_boost = (
        lap >= total - 1
        and state["boost_available"]
        and state["position"] > 1
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
