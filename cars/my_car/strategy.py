"""Strategy — pit wall decisions each tick.

Receives: state (dict) with fields including:
  tire_wear (float 0-1), pit_stops (int), lap (int), total_laps (int),
  fuel_remaining (float kg), position (int), gap_ahead_s (float),
  speed (float km/h), curvature (float), tire_compound (str)

Returns: dict with decisions. Only include fields you want to change:
  pit_request (bool), tire_compound_request (str),
  engine_mode (str: "push"/"standard"/"conserve")

Better code would plan pit windows based on tire degradation rate,
switch to conserve mode when fuel is low, and push when gaps are small.
"""


def strategy(state):
    if state.get("tire_wear", 0) > 0.7 and state.get("pit_stops", 0) == 0:
        return {"pit_request": True, "tire_compound_request": "hard"}
    return {"engine_mode": "standard"}
