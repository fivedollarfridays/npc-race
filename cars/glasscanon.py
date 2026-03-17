"""GlassCanon -- Yolo speed.
0-stop preferred on hards. Emergency pit if tire_wear > 0.80.
Full push always. Blocks on straights. Learns 0-stop vs 1-stop per track."""

import json

CAR_NAME = "GlassCanon"
CAR_COLOR = "#ffcc00"

POWER = 40
GRIP = 15
WEIGHT = 10
AERO = 20
BRAKES = 15

_data = None
_last_race = -1
_force_pit = False


def _ensure_data(state):
    global _data, _last_race, _force_pit
    rn = state.get("race_number", 1)
    if _data is not None and rn == _last_race:
        return
    _last_race = rn
    _data = {}
    if state.get("data_file"):
        try:
            with open("cars/data/GlassCanon.json") as f:
                _data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    track = state.get("track_name") or "unknown"
    td = _data.get(track, {})
    if td.get("races", 0) >= 3:
        _force_pit = td.get("1stop_avg_pos", 99) < td.get("0stop_avg_pos", 99)
    else:
        _force_pit = False


def _save():
    if not _data:
        return
    try:
        with open("cars/data/GlassCanon.json", "w") as f:
            json.dump(_data, f, indent=2)
    except OSError:
        pass


def strategy(state):
    _ensure_data(state)
    tire_wear = state["tire_wear"]
    pit_stops = state["pit_stops"]
    curv = state["curvature"]
    track = state.get("track_name") or "unknown"

    pit_request = False
    compound_req = None
    if pit_stops == 0 and ((_force_pit and tire_wear > 0.50) or tire_wear > 0.80):
        pit_request = True
        compound_req = "hard"

    in_curve = curv > 0.08
    throttle = 0.85 if in_curve else 1.0

    lateral = 0.0
    behind = [c for c in state["nearby_cars"] if c["distance_ahead"] < 0]
    if not in_curve and behind and state["gap_behind_s"] < 1.0:
        lateral = max(behind, key=lambda c: c["distance_ahead"])["lateral"]

    use_boost = (
        state["boost_available"]
        and state["lap"] >= state["total_laps"] - 1 and not in_curve
    )

    # Save learning on last lap
    if state.get("data_file") and state["lap"] >= state["total_laps"] - 1:
        td = _data.setdefault(track, {"0stop_avg_pos": 0, "1stop_avg_pos": 0, "races": 0})
        pos = state["position"]
        key = "1stop_avg_pos" if pit_stops > 0 else "0stop_avg_pos"
        n = td.get("races", 0)
        td[key] = (td.get(key, 0) * n + pos) / (n + 1) if n > 0 else pos
        td["races"] = n + 1
        _save()

    return {
        "throttle": throttle, "boost": use_boost, "tire_mode": "push",
        "lateral_target": lateral, "pit_request": pit_request,
        "tire_compound_request": compound_req, "engine_mode": "push",
    }
