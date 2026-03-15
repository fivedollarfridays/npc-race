"""
NPC Race — Car Template
========================
Copy this file, rename it, and make it yours.

RULES:
  - Budget: 100 points total across POWER, GRIP, WEIGHT, AERO, BRAKES
  - Going over budget disqualifies your car
  - strategy() is called every tick — return your decisions
  - Same driver AI for everyone. Your car is the only difference.

STATS:
  POWER   → Top speed and acceleration. More = faster straights.
  GRIP    → Cornering ability. More = higher speed through curves.
  WEIGHT  → Heavy = slower accel but better drafting resistance.
            Light = quicker but more affected by draft.
  AERO    → Drafting bonus when behind other cars. High speed stability.
  BRAKES  → Braking power. More = later braking into corners.

STRATEGY STATE (what you get each tick):
  speed           → Your current speed
  position        → Your race position (1 = first)
  total_cars      → Number of cars in race
  lap             → Current lap (0-indexed)
  total_laps      → Total laps in race
  tire_wear       → 0.0 (fresh) to 1.0 (destroyed)
  boost_available → True if you haven't used boost yet
  boost_active    → True if boost is currently firing
  curvature       → Track curvature at your position (0 = straight, higher = tighter)
  nearby_cars     → List of nearby cars with:
                      name, distance_ahead, speed, lateral
  distance        → Total distance traveled
  track_length    → Length of one lap
  lateral         → Your lateral position (-1 to 1)

STRATEGY RETURNS:
  throttle    → 0.0 to 1.0 (how hard to push)
  boost       → True to activate boost (one-time use, 3 seconds)
  tire_mode   → "conserve" | "balanced" | "push"
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
