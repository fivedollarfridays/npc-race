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
  speed           float   Your current speed (units/sec, typically 40-300)
  position        int     Your race position (1 = first place)
  total_cars      int     Number of cars in the race
  lap             int     Current lap (0-indexed, so lap 0 = first lap)
  total_laps      int     Total laps in the race
  tire_wear       float   0.0 (fresh) to 1.0 (destroyed). Affects grip.
  boost_available bool    True if you have not used your boost yet
  boost_active    bool    True if your boost is currently firing
  curvature       float   Track curvature at your position.
                          0.0 = straight, higher = tighter corner.
  nearby_cars     list    Cars within 100 units of you. Each entry is a dict:
                            name           str    Car name
                            distance_ahead float  Positive = ahead, negative = behind
                            speed          float  Their current speed
                            lateral        float  Their lane position (-1 to 1)
  distance        float   Total distance you have traveled (units)
  track_length    float   Length of one full lap (units)
  lateral         float   Your lateral lane position (-1.0 to 1.0)

STRATEGY RETURNS (dict)
-----------------------
  throttle   float   0.0 (coast) to 1.0 (full throttle). Default: 1.0
  boost      bool    True to activate boost. One-time use, lasts 3 seconds.
                     Gives 1.25x top speed while active. Default: False
  tire_mode  str     One of:
                       "conserve"  -- Low wear (0.00008/tick), saves tires
                       "balanced"  -- Normal wear (0.00018/tick)
                       "push"      -- High wear (0.00035/tick), max grip
                     Default: "balanced"

If strategy() raises an exception or returns a non-dict, defaults are used.
"""

CAR_NAME = "MyCar"
CAR_COLOR = "#00ff88"

# Budget: 100 points. Allocate wisely.
POWER = 20
GRIP = 20
WEIGHT = 20
AERO = 20
BRAKES = 20


def strategy(state):
    return {
        "throttle": 1.0,
        "boost": state["lap"] >= state["total_laps"] - 1,
        "tire_mode": "balanced",
    }


# -----------------------------------------------------------------------
# Example strategies (uncomment one to try it, or use as inspiration)
# -----------------------------------------------------------------------

# --- Example 1: Defensive / tire-saver ---
# Conserves tires early, pushes on the last lap, saves boost for the finish.
#
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
# Pushes hard from the start. Burns tires but builds an early lead.
#
# def strategy(state):
#     in_corner = state["curvature"] > 0.02
#     throttle = 0.9 if in_corner else 1.0
#
#     # Boost on lap 1 to get ahead of the pack
#     use_boost = state["lap"] == 0 and state["boost_available"]
#
#     return {"throttle": throttle, "boost": use_boost, "tire_mode": "push"}

# --- Example 3: Draft-and-pass ---
# Sits behind opponents to draft, then passes on straights.
#
# def strategy(state):
#     cars_ahead = [c for c in state["nearby_cars"] if c["distance_ahead"] > 0]
#     drafting = any(5 < c["distance_ahead"] < 40 for c in cars_ahead)
#     on_straight = state["curvature"] < 0.005
#     last_lap = state["lap"] >= state["total_laps"] - 1
#
#     if drafting and on_straight and last_lap:
#         # Slingshot pass
#         throttle = 1.0
#         tire_mode = "push"
#     elif drafting:
#         # Tuck in and save tires
#         throttle = 0.95
#         tire_mode = "conserve"
#     else:
#         throttle = 1.0
#         tire_mode = "balanced"
#
#     use_boost = last_lap and on_straight and state["boost_available"]
#     return {"throttle": throttle, "boost": use_boost, "tire_mode": tire_mode}
