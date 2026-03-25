"""Strategy — pit wall decisions each tick.

Called every tick with a state dict containing:
    tire_wear        (float 0-1)   how worn tires are (1.0 = destroyed)
    position         (int)         current race position
    lap              (int)         current lap number
    total_laps       (int)         total laps in the race
    gap_ahead_s      (float)       gap to car ahead in seconds
    gap_behind_s     (float)       gap to car behind in seconds
    fuel_remaining   (float)       fuel remaining in kg
    tire_compound    (str)         current compound: soft/medium/hard
    engine_mode      (str)         current mode: push/standard/conserve
    elapsed_s        (float)       elapsed race time in seconds
    speed            (float)       current speed in km/h
    curvature        (float)       track curvature at current position
    pit_stops        (int)         number of pit stops so far

Return: dict with any of these decision fields (omit fields to keep
current values):
    pit_request             (bool)   request a pit stop
    tire_compound_request   (str)    soft / medium / hard
    engine_mode             (str)    push / standard / conserve
    boost                   (bool)   activate short-term power boost
    tire_mode               (str)    push / balanced / conserve
    throttle                (float)  override throttle 0.0-1.0
    lateral_target          (float)  lateral position -1.0 to 1.0
    drs_request             (bool)   request DRS activation
    ers_deploy_mode         (str)    attack / balanced / harvest

Improvement ideas:
- Plan pit windows based on tire degradation rate
- Switch to conserve mode when fuel is low
- Push when the gap to the car ahead is small
"""


def strategy(state):
    if state.get("tire_wear", 0) > 0.7 and state.get("pit_stops", 0) == 0:
        return {"pit_request": True, "tire_compound_request": "hard"}
    return {"engine_mode": "standard"}
