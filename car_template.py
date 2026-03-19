"""
NPC Race -- Car Template
========================
Copy this file, rename it, and make it yours.

RULES
-----
  - Budget: 100 points total across POWER, GRIP, WEIGHT, AERO, BRAKES
  - Sum of all five stats must be <= 100 or your car is disqualified
  - strategy() is called every tick (30 ticks/sec) -- return your decisions
  - Same driver AI for everyone. Your car build is the only difference.

STATS (int, each 0-100, sum <= 100)
------------------------------------
  POWER   -- Top speed and acceleration. More = faster on straights.
  GRIP    -- Cornering ability. More = higher speed through curves.
  WEIGHT  -- Heavy = slower accel but better drafting resistance.
              Light = quicker but more affected by draft.
  AERO    -- Drafting bonus when behind other cars. High-speed stability.
  BRAKES  -- Braking power. More = later braking into corners.

STRATEGY STATE (dict passed to strategy() each tick)
-----------------------------------------------------
  speed           float   Your current speed (km/h, typically 40-300)
  position        int     Your race position (1 = first place)
  total_cars      int     Number of cars in the race
  lap             int     Current lap (0-indexed, so lap 0 = first lap)
  total_laps      int     Total laps in the race
  tire_wear       float   0.0 (fresh) to 1.0 (destroyed). Affects grip.
  boost_available bool    True if you have not used your boost yet
  boost_active    bool    True if your boost is currently firing
  curvature       float   Track curvature (0.0 = straight, higher = tighter corner)
  nearby_cars     list    Cars within 100 units of you. Each entry is a dict:
                            name           str    Car name
                            distance_ahead float  Positive = ahead, negative = behind
                            speed          float  Their current speed
                            lateral        float  Their lane position (-1 to 1)
  distance        float   Total distance you have traveled (units)
  track_length    float   Length of one full lap (units)
  lateral         float   Your lateral lane position (-1.0 to 1.0)
  fuel_remaining  float   Fuel in kg remaining
  fuel_pct        float   0.0-1.0 percentage of starting fuel remaining
  tire_compound   str     Current tire compound ("soft"/"medium"/"hard")
  tire_age_laps   int     Laps since last tire change
  engine_mode     str     Current engine mode ("push"/"standard"/"conserve")
  pit_status      str     "racing", "pit_entry", "pit_stationary", "pit_exit"
  pit_stops       int     Number of pit stops completed
  gap_ahead_s     float   Gap to car ahead in seconds (0.0 if leading)
  gap_behind_s    float   Gap to car behind in seconds (0.0 if last)

SPRINT 5: TIER 2 REALISM
  tire_temp       float   Tire surface temp (C). Optimal: soft 90, medium 80, hard 70.
  in_drs_zone     bool    Car is in a DRS activation zone.
  drs_available   bool    DRS not yet used this lap.
  drs_active      bool    DRS currently open.
  current_setup   dict    Read-only view of your SETUP configuration.

SPRINT 9: COLLISIONS & SAFETY CAR
  damage float 0.0-1.0 accumulated damage. safety_car bool, safety_car_laps int
  in_spin bool — currently recovering from a spin
SPRINT 10: WEATHER
  track_wetness float 0-1. weather_forecast list [(lap, wetness),...]. weather_state str
  tire_compound str — also "intermediate" (best ~0.45) and "wet" (best 0.6+)
SPRINT 11: ERS + BRAKES
  ers_energy float 0-4 MJ. ers_deploy_mode str. brake_temp float (fade >700C)

STRATEGY RETURNS (dict)
-----------------------
  throttle              float   0.0 (coast) to 1.0 (full throttle). Default: 1.0
  boost                 bool    True to activate boost. One-time use, lasts 3 sec.
                                Gives 1.25x top speed while active. Default: False
  tire_mode             str     One of: "conserve", "balanced", "push".
                                Modulates tire wear rate. Default: "balanced"
  lateral_target        float   Target lateral position. -1.0=inside, 0.0=center,
                                1.0=outside. Clamped to [-1, 1]. Default: 0.0
  pit_request           bool    True to request a pit stop. Default: False
  tire_compound_request str     Compound for next pit stop: "soft", "medium",
                                or "hard". Ignored if pit_request is False.
                                Default: None (no change)
  engine_mode           str     "push" (fast, burns more fuel),
                                "standard" (balanced),
                                "conserve" (slow, saves fuel). Default: "standard"
  drs_request           bool    Request DRS activation (in_drs_zone + gap < 1.0)
  ers_deploy_mode       str     "attack" (+8 km/h), "balanced" (+4), "harvest" (recharge)

If strategy() raises an exception or returns a non-dict, defaults are used.
Partial returns are merged with defaults -- you only need to return fields you change.

LEVEL 2: CROSS-RACE LEARNING (state fields)
  data_file       str|None   Path to car's persistent JSON file (use load_data/save_data)
  race_number     int        Race number in tournament sequence (1-indexed)
  track_name      str|None   Track preset name (None for procedural)
"""

import json

CAR_NAME = "MyCar"
CAR_COLOR = "#00ff88"

# Budget: 100 points. Allocate wisely.
POWER = 20
GRIP = 20
WEIGHT = 20
AERO = 20
BRAKES = 20

# Optional: Pre-race setup sliders (all default to 0.0 if omitted -- backward compatible)
# SETUP = {
#     "wing_angle":    0.0,   # -1.0 (low drag/faster straights) to +1.0 (high downforce/better corners)
#     "brake_bias":    0.5,   # 0.3 (rear-biased) to 0.7 (front-biased). Optimal ~0.58.
#     "suspension":    0.0,   # -1.0 (soft, less tire heat) to +1.0 (stiff, more tire heat)
#     "tire_pressure": 0.0,   # -1.0 (cooler tires, more rolling resistance) to +1.0 (hotter, less drag)
# }


def strategy(state):
    return {
        "throttle": 1.0,
        "boost": state["lap"] >= state["total_laps"] - 1,
        "tire_mode": "balanced",
        "engine_mode": "standard",
    }


# -----------------------------------------------------------------------
# Example strategies (uncomment one to try it, or use as inspiration)
# -----------------------------------------------------------------------

# --- Example 1: Defensive / tire-saver ---
# def strategy(state):
#     last_lap = state["lap"] >= state["total_laps"] - 1
#     worn_out = state["tire_wear"] > 0.6
#     in_corner = state["curvature"] > 0.01
#
#     if last_lap:
#         tire_mode = "push"
#         throttle = 1.0
#     elif worn_out or in_corner:
#         tire_mode = "conserve"
#         throttle = 0.85
#     else:
#         tire_mode = "balanced"
#         throttle = 0.95
#
#     use_boost = last_lap and state["boost_available"]
#     return {"throttle": throttle, "boost": use_boost, "tire_mode": tire_mode}

# --- Example 2: Aggressive / full-send ---
# def strategy(state):
#     in_corner = state["curvature"] > 0.02
#     throttle = 0.9 if in_corner else 1.0
#
#     # Boost on lap 1 to get ahead of the pack
#     use_boost = state["lap"] == 0 and state["boost_available"]
#
#     return {"throttle": throttle, "boost": use_boost, "tire_mode": "push"}
# --- Example 3: Pit stop strategy ---
# def strategy(state):
#     need_pit = state["lap"] >= state["total_laps"] // 2 and state["pit_stops"] == 0
#     engine_mode = "conserve" if state["fuel_pct"] < 0.3 else "standard"
#     return {
#         "throttle": 1.0, "boost": state["lap"] >= state["total_laps"] - 1,
#         "tire_mode": "balanced", "pit_request": need_pit,
#         "tire_compound_request": "medium" if need_pit else None,
#         "engine_mode": engine_mode,
#     }

# --- Example 4: Draft-and-pass with lateral movement ---
# def strategy(state):
#     cars_ahead = [c for c in state["nearby_cars"] if c["distance_ahead"] > 0]
#     drafting = any(5 < c["distance_ahead"] < 40 for c in cars_ahead)
#     on_straight = state["curvature"] < 0.005
#     lateral = 1.0 if drafting and on_straight else (-1.0 if state["curvature"] > 0.01 else 0.0)
#     last_lap = state["lap"] >= state["total_laps"] - 1
#     return {
#         "throttle": 1.0, "boost": last_lap and on_straight and state["boost_available"],
#         "tire_mode": "push" if last_lap else "balanced", "lateral_target": lateral,
#     }

# --- Level 2: Cross-Race Learning Helpers ---

def load_data(path: str | None) -> dict:
    """Load car's persistent data. Returns {} if no data yet."""
    if path is None:
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(path: str | None, data: dict) -> None:
    """Save car's persistent data."""
    if path is None:
        return
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
