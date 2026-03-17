"""Silky -- The corner carver.
1-stop: soft -> medium. Conserve first stint, standard on mediums.
Inside line in corners, blocks on straights. Learns compound order per track."""

import json

CAR_NAME = "Silky"
CAR_COLOR = "#aa44ff"

POWER = 15
GRIP = 35
WEIGHT = 15
AERO = 15
BRAKES = 20

_data = None
_last_race = -1
_use_medium_first = False


def _ensure_data(state):
    global _data, _last_race, _use_medium_first
    rn = state.get("race_number", 1)
    if _data is not None and rn == _last_race:
        return
    _last_race = rn
    _data = {}
    if state.get("data_file"):
        try:
            with open("cars/data/Silky.json") as f:
                _data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    track = state.get("track_name") or "unknown"
    td = _data.get(track, {})
    if td.get("races", 0) >= 3:
        _use_medium_first = td.get("medium_first_avg", 99) < td.get("soft_first_avg", 99)
    else:
        _use_medium_first = False


def _save():
    if not _data:
        return
    try:
        with open("cars/data/Silky.json", "w") as f:
            json.dump(_data, f, indent=2)
    except OSError:
        pass


def strategy(state):
    _ensure_data(state)
    tire_wear = state["tire_wear"]
    pit_stops = state["pit_stops"]
    curv = state["curvature"]
    gap_behind = state["gap_behind_s"]
    nearby = state["nearby_cars"]
    track = state.get("track_name") or "unknown"

    pit_request = False
    compound_req = None
    second = "soft" if _use_medium_first else "medium"
    if pit_stops == 0 and tire_wear > 0.72:
        pit_request = True
        compound_req = second

    engine_mode = "conserve" if pit_stops == 0 else "standard"
    in_corner = curv > 0.05
    throttle = 0.9 if in_corner else 1.0

    lateral = 0.0
    if curv > 0.05:
        lateral = -1.0
    else:
        behind = [c for c in nearby if c["distance_ahead"] < 0]
        if gap_behind < 1.0 and behind:
            lateral = max(behind, key=lambda c: c["distance_ahead"])["lateral"]

    use_boost = (
        state["boost_available"] and curv > 0.1
        and state["lap"] >= state["total_laps"] - 1
    )

    # Save learning on last lap
    if state.get("data_file") and state["lap"] >= state["total_laps"] - 1:
        td = _data.setdefault(track, {"soft_first_avg": 0, "medium_first_avg": 0, "races": 0})
        pos = state["position"]
        key = "medium_first_avg" if _use_medium_first else "soft_first_avg"
        n = td.get("races", 0)
        td[key] = (td.get(key, 0) * n + pos) / (n + 1) if n > 0 else pos
        td["races"] = n + 1
        _save()

    return {
        "throttle": throttle, "boost": use_boost, "tire_mode": "balanced",
        "lateral_target": lateral, "pit_request": pit_request,
        "tire_compound_request": compound_req, "engine_mode": engine_mode,
    }
