"""GooseLoose -- balanced, smart fuel, SC-aware. All-rounder."""
import json
CAR_NAME = "GooseLoose"
CAR_COLOR = "#ff6600"
POWER = 25
GRIP = 25
WEIGHT = 15
AERO = 20
BRAKES = 15
ENGINE_SPEC, AERO_SPEC, CHASSIS_SPEC = "v6_1000hp", "medium_downforce", "standard"
SETUP = {"wing_angle": -0.2, "brake_bias": 0.55, "suspension": 0.1, "tire_pressure": 0.0}
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
    global _saved
    _ensure_data(state)
    tire_wear = state["tire_wear"]
    pit_stops = state["pit_stops"]
    position = state["position"]
    gap_ahead = state["gap_ahead_s"]
    gap_behind = state["gap_behind_s"]
    curv = state["curvature"]
    track = state.get("track_name") or "unknown"
    if state.get("data_file") and state["lap"] >= state["total_laps"] - 1 and not _saved:
        td = _data.setdefault(track, {"opponent_speeds": {}, "races": 0})
        td["opponent_speeds"].update({c["name"]: c["speed"] for c in state["nearby_cars"]})
        td["races"], td["last_position"], _saved = td.get("races", 0) + 1, position, True
        _save()
    pit_request, compound_req = False, None
    tire_temp = state.get("tire_temp", 20.0)
    sc_active, wetness = state.get("safety_car", False), state.get("track_wetness", 0.0)
    compound = state.get("tire_compound", "medium")
    if wetness > 0.7 and compound != "wet":
        pit_request, compound_req = True, "wet"
    elif wetness > 0.4 and compound in ("soft", "medium", "hard"):
        pit_request, compound_req = True, "intermediate"
    elif wetness < 0.15 and compound in ("intermediate", "wet"):
        pit_request, compound_req = True, "medium"
    elif pit_stops == 0 and sc_active and tire_wear > 0.3:
        pit_request, compound_req = True, "hard"
    elif pit_stops == 0 and (tire_wear > 0.70 or (tire_temp > 105.0 and tire_wear > 0.55)):
        pit_request, compound_req = True, "hard"
    if position == 1 and gap_behind > 3.0:
        engine_mode = "conserve"
    elif gap_ahead < 2.0:
        engine_mode = "push"
    else:
        engine_mode = "standard"
    throttle = 0.75 if curv > 0.1 else 1.0
    lateral = _lateral_decision(curv, gap_behind, state["nearby_cars"])
    use_boost = (state["lap"] >= state["total_laps"] - 1
                 and state["boost_available"] and position > 1)
    ers = state.get("ers_energy", 4.0)
    ers_mode = "attack" if position > 2 and gap_ahead < 2.0 and ers > 1.0 else ("harvest" if ers < 0.5 else "balanced")
    return {
        "throttle": throttle, "boost": use_boost, "tire_mode": "balanced",
        "lateral_target": lateral, "pit_request": pit_request,
        "tire_compound_request": compound_req, "engine_mode": engine_mode,
        "ers_deploy_mode": ers_mode,
    }
