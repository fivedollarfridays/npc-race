"""
SlipStream — The drafter.
1-stop: medium -> soft (late undercut). Sits in draft of car ahead.
Standard engine while drafting, push on fresh softs. Slingshot strategy.
"""

CAR_NAME = "SlipStream"
CAR_COLOR = "#00aaff"

POWER = 20
GRIP = 15
WEIGHT = 15
AERO = 35
BRAKES = 15


def _draft_info(nearby):
    """Analyze nearby cars for drafting opportunities."""
    cars_ahead = [c for c in nearby if c["distance_ahead"] > 0]
    drafting = any(5 < c["distance_ahead"] < 35 for c in cars_ahead)
    lateral = 0.0
    if cars_ahead:
        closest = min(cars_ahead, key=lambda c: c["distance_ahead"])
        lateral = closest["lateral"]
    return cars_ahead, drafting, lateral


def strategy(state):
    lap = state["lap"]
    total = max(state["total_laps"], 1)
    lap_pct = lap / total
    pit_stops = state["pit_stops"]
    compound = state["tire_compound"]

    _, drafting, draft_lateral = _draft_info(state["nearby_cars"])

    # --- Pit strategy: 1-stop at ~55% for fresh softs ---
    pit_request = pit_stops == 0 and lap_pct >= 0.50
    compound_req = "soft" if pit_request else None

    # --- Engine mode: push on fresh softs, standard otherwise ---
    on_fresh_softs = compound == "soft" and pit_stops >= 1
    engine_mode = "push" if on_fresh_softs else "standard"

    # --- Throttle: sit tight in draft range ---
    throttle = 0.95 if (drafting and state["position"] > 1) else 1.0

    # --- Boost when close behind on last lap ---
    use_boost = lap >= total - 1 and state["boost_available"] and drafting

    return {
        "throttle": throttle,
        "boost": use_boost,
        "tire_mode": "balanced",
        "lateral_target": draft_lateral,
        "pit_request": pit_request,
        "tire_compound_request": compound_req,
        "engine_mode": engine_mode,
    }
