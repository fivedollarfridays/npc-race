"""
Silky — The corner carver.
1-stop: soft -> medium. Takes inside line through corners.
Conserves engine to extend stint. Good corner throttle management.
"""

CAR_NAME = "Silky"
CAR_COLOR = "#aa44ff"

POWER = 15
GRIP = 35
WEIGHT = 15
AERO = 15
BRAKES = 20


def strategy(state):
    lap = state["lap"]
    total = max(state["total_laps"], 1)
    lap_pct = lap / total
    pit_stops = state["pit_stops"]
    curv = state["curvature"]

    # --- Pit strategy: 1-stop at ~35% (softs wear fast) ---
    pit_request = False
    compound_req = None
    if pit_stops == 0 and lap_pct >= 0.30:
        pit_request = True
        compound_req = "medium"

    # --- Engine mode: conserve to extend stint ---
    engine_mode = "conserve"

    # --- Throttle: high grip lets us stay on throttle in corners ---
    throttle = 1.0 if curv < 0.3 else 0.85

    # --- Lateral: take inside line in corners, center on straights ---
    if curv > 0.05:
        lateral = -1.0  # inside line
    else:
        lateral = 0.0

    # --- Boost in tight section on last lap ---
    use_boost = (
        state["boost_available"]
        and curv > 0.1
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
