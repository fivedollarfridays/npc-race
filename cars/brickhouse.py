"""BrickHouse -- The brute.
2-stop: soft -> medium -> hard. Push when behind, conserve when leading.
Heavy car needs caution in corners. Learns optimal pit wear threshold."""

import json

CAR_NAME = "BrickHouse"
CAR_COLOR = "#cc2222"

POWER = 35
GRIP = 10
WEIGHT = 25
AERO = 15
BRAKES = 15

_data = None
_last_race = -1
_threshold_1 = 0.65
_threshold_2 = 0.70


def _ensure_data(state):
    global _data, _last_race, _threshold_1, _threshold_2
    rn = state.get("race_number", 1)
    if _data is not None and rn == _last_race:
        return
    _last_race = rn
    _data = {}
    if state.get("data_file"):
        try:
            with open("cars/data/BrickHouse.json") as f:
                _data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    track = state.get("track_name") or "unknown"
    td = _data.get(track, {})
    _threshold_1 = td.get("best_threshold", 0.65)
    _threshold_2 = td.get("threshold_2", 0.70)


def _save():
    if not _data:
        return
    try:
        with open("cars/data/BrickHouse.json", "w") as f:
            json.dump(_data, f, indent=2)
    except OSError:
        pass


def _pit_decision(tire_wear, pit_stops):
    if tire_wear > 0.85:
        return True, "hard" if pit_stops >= 1 else "medium"
    if pit_stops == 0 and tire_wear > _threshold_1:
        return True, "medium"
    if pit_stops == 1 and tire_wear > _threshold_2:
        return True, "hard"
    return False, None


def strategy(state):
    _ensure_data(state)
    curv = state["curvature"]
    position = state["position"]
    gap_behind = state["gap_behind_s"]
    track = state.get("track_name") or "unknown"

    pit_request, compound_req = _pit_decision(state["tire_wear"], state["pit_stops"])
    engine_mode = "push" if position > 1 else "conserve"
    throttle = 0.75 if curv > 0.08 else 1.0

    lateral = 0.0
    behind = [c for c in state["nearby_cars"] if c["distance_ahead"] < 0]
    if gap_behind < 1.5 and behind:
        lateral = max(behind, key=lambda c: c["distance_ahead"])["lateral"]

    use_boost = (
        state["boost_available"] and curv < 0.08
        and position > 2 and state["lap"] >= state["total_laps"] - 1
    )

    # Save learning on last lap
    if state.get("data_file") and state["lap"] >= state["total_laps"] - 1:
        td = _data.setdefault(track, {})
        old_best = td.get("best_position", 99)
        if position <= old_best:
            td["best_position"] = position
            td["best_threshold"] = _threshold_1
            td["threshold_2"] = _threshold_2
        elif td.get("races", 0) > 2:
            td["best_threshold"] = max(0.50, _threshold_1 - 0.05)
        td["races"] = td.get("races", 0) + 1
        _save()

    return {
        "throttle": throttle, "boost": use_boost, "tire_mode": "balanced",
        "lateral_target": lateral, "pit_request": pit_request,
        "tire_compound_request": compound_req, "engine_mode": engine_mode,
    }
