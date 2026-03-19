"""SlipStream -- 1-stop M->S drafter, damage-aware conserve mode."""

import json

CAR_NAME = "SlipStream"
CAR_COLOR = "#00aaff"

POWER = 20
GRIP = 15
WEIGHT = 15
AERO = 35
BRAKES = 15

SETUP = {"wing_angle": -0.4, "brake_bias": 0.5, "suspension": -0.1, "tire_pressure": 0.0}

_data = None
_last_race = -1
_saved = False


def _ensure_data(state):
    global _data, _last_race, _saved
    rn = state.get("race_number", 1)
    if _data is not None and rn == _last_race:
        return
    _last_race = rn
    _data = {}
    _saved = False
    if state.get("data_file"):
        try:
            with open("cars/data/SlipStream.json") as f:
                _data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass


def _save():
    if not _data:
        return
    try:
        with open("cars/data/SlipStream.json", "w") as f:
            json.dump(_data, f, indent=2)
    except OSError:
        pass


def _draft_info(nearby):
    cars_ahead = [c for c in nearby if c["distance_ahead"] > 0]
    lateral = 0.0
    if cars_ahead:
        lateral = min(cars_ahead, key=lambda c: c["distance_ahead"])["lateral"]
    return cars_ahead, lateral


def strategy(state):
    global _saved
    _ensure_data(state)
    tire_wear = state["tire_wear"]
    pit_stops = state["pit_stops"]
    compound = state["tire_compound"]
    gap_ahead = state["gap_ahead_s"]
    curv = state["curvature"]
    track = state.get("track_name") or "unknown"
    cars_ahead, draft_lateral = _draft_info(state["nearby_cars"])
    drafting = gap_ahead < 5.0 and len(cars_ahead) > 0
    pit_request = False
    compound_req = None
    if pit_stops == 0 and tire_wear > 0.68 and gap_ahead > 18:
        pit_request = True
        compound_req = "soft"
    on_fresh_softs = compound == "soft" and pit_stops >= 1
    if state.get("damage", 0) > 0.3:
        engine_mode = "conserve"
    elif on_fresh_softs and gap_ahead < 3.0:
        engine_mode = "push"
    else:
        engine_mode = "standard"
    in_corner = curv > 0.08
    throttle = 0.7 if in_corner else 1.0
    lateral = draft_lateral if drafting else 0.0
    use_boost = (
        state["lap"] >= state["total_laps"] - 1
        and state["boost_available"] and gap_ahead < 3.0
    )
    if state.get("data_file") and state["lap"] >= state["total_laps"] - 1 and not _saved:
        td = _data.setdefault(track, {"draft_positions": [], "no_draft_positions": []})
        pos = state["position"]
        (td["draft_positions"] if drafting else td["no_draft_positions"]).append(pos)
        _save()
        _saved = True
    drs_req = (state.get("in_drs_zone", False) and state.get("gap_ahead_s", 99) < 1.0
               and state.get("drs_available", False))
    return {
        "throttle": throttle, "boost": use_boost, "tire_mode": "balanced",
        "lateral_target": lateral, "pit_request": pit_request,
        "tire_compound_request": compound_req, "engine_mode": engine_mode,
        "drs_request": drs_req,
    }
