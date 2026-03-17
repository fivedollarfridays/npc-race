"""GooseLoose -- The founder car.
1-stop: medium -> hard. Position-aware engine modes.
Inside line in corners, defends on straights. Learns opponent speed patterns."""

import json

CAR_NAME = "GooseLoose"
CAR_COLOR = "#ff6600"

POWER = 25
GRIP = 25
WEIGHT = 15
AERO = 20
BRAKES = 15

_data = None
_last_race = -1


def _ensure_data(state):
    global _data, _last_race
    rn = state.get("race_number", 1)
    if _data is not None and rn == _last_race:
        return
    _last_race = rn
    _data = {}
    if state.get("data_file"):
        try:
            with open("cars/data/GooseLoose.json") as f:
                _data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass


def _save():
    if not _data:
        return
    try:
        with open("cars/data/GooseLoose.json", "w") as f:
            json.dump(_data, f, indent=2)
    except OSError:
        pass


def _lateral_decision(curv, gap_behind, nearby):
    if curv > 0.1:
        return -0.5
    behind = [c for c in nearby if c["distance_ahead"] < 0]
    if gap_behind < 1.0 and behind:
        return max(behind, key=lambda c: c["distance_ahead"])["lateral"]
    return 0.0


def strategy(state):
    _ensure_data(state)
    tire_wear = state["tire_wear"]
    pit_stops = state["pit_stops"]
    position = state["position"]
    gap_ahead = state["gap_ahead_s"]
    gap_behind = state["gap_behind_s"]
    curv = state["curvature"]
    track = state.get("track_name") or "unknown"

    # Record opponent speeds on last lap
    if state.get("data_file") and state["lap"] >= state["total_laps"] - 1:
        td = _data.setdefault(track, {"opponent_speeds": {}, "races": 0})
        for car in state["nearby_cars"]:
            td["opponent_speeds"][car["name"]] = car["speed"]
        td["races"] = td.get("races", 0) + 1
        td["last_position"] = position
        _save()

    pit_request = False
    compound_req = None
    if pit_stops == 0 and tire_wear > 0.70:
        pit_request = True
        compound_req = "hard"

    if position == 1 and gap_behind > 3.0:
        engine_mode = "conserve"
    elif gap_ahead < 2.0:
        engine_mode = "push"
    else:
        engine_mode = "standard"

    throttle = 0.75 if curv > 0.1 else 1.0
    lateral = _lateral_decision(curv, gap_behind, state["nearby_cars"])
    use_boost = (
        state["lap"] >= state["total_laps"] - 1
        and state["boost_available"] and position > 1
    )
    return {
        "throttle": throttle, "boost": use_boost, "tire_mode": "balanced",
        "lateral_target": lateral, "pit_request": pit_request,
        "tire_compound_request": compound_req, "engine_mode": engine_mode,
    }
