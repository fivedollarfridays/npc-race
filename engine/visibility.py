"""Opponent visibility model — defines observable vs hidden car data."""

# Fields visible to opponents (cockpit/TV observables)
OBSERVABLE_FIELDS = {
    "name", "position", "speed", "lateral", "tire_compound",
    "tire_age_laps", "pit_stops", "drs_active", "in_spin", "finished",
    "gap_ahead_s", "lap",
}

# Fields only available for your own car (private telemetry)
PRIVATE_FIELDS = {
    "tire_wear", "fuel_remaining", "fuel_pct", "tire_temp", "engine_mode",
    "damage", "ers_energy", "ers_deploy_mode", "brake_temp", "spin_risk",
    "dirty_air_factor", "boost_available", "boost_active",
}

# Allowed keys in nearby_cars (distance_ahead is a computed proximity field)
NEARBY_ALLOWED = {"name", "distance_ahead", "speed", "lateral",
                  "tire_compound", "tire_age_laps"}


def build_opponent_info(all_states: list[dict], my_car_idx: int,
                        positions: dict, timings: dict,
                        ticks_per_sec: int, tick: int) -> list[dict]:
    """Build list of opponent dicts with observable-only fields."""
    result = []
    for s in all_states:
        if s["car_idx"] == my_car_idx:
            continue
        ps = s.get("pit_state", {})
        result.append({
            "name": s["name"],
            "position": positions.get(s["car_idx"], 0),
            "speed": round(s["speed"], 1),
            "lateral": round(s.get("lateral", 0.0), 2),
            "lap": s.get("lap", 0),
            "tire_compound": s.get("tire_compound", "medium"),
            "tire_age_laps": s.get("tire_age_laps", 0),
            "pit_stops": ps.get("pit_stops", 0) if isinstance(ps, dict) else 0,
            "drs_active": bool(s.get("drs_active", False)),
            "in_spin": s.get("spin_recovery", 0) > 0,
            "finished": bool(s.get("finished", False)),
        })
    return result


def filter_nearby_cars(nearby: list[dict]) -> list[dict]:
    """Filter nearby_cars to observable fields only."""
    return [{k: v for k, v in car.items() if k in NEARBY_ALLOWED} for car in nearby]
