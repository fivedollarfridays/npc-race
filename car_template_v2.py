"""
NPC Race — Car Template v2
===========================
Copy this file, rename it, and make it yours.

You're building a car out of code. Each function below IS a real car part.
The F1 driver handles braking points and racing line.
You engineer the machine underneath.

HARDWARE SPECS (pick your base hardware — sets the limits your code operates in)
  ENGINE_SPEC:  "v6_1000hp" (1000 HP ceiling)
  AERO_SPEC:    "low_drag" / "medium_downforce" / "high_downforce"
  CHASSIS_SPEC: "standard" (798 kg) / "lightweight" (785 kg)

YOUR CODE (10 part functions — each IS a car part)
  POWERTRAIN:    engine_map, gearbox, fuel_mix
  HYBRID SYSTEM: ers_deploy, ers_harvest
  CHASSIS:       suspension, brake_bias, cooling, differential
  PIT WALL:      strategy

If a part function is missing, the default is used.
If your code crashes, the default takes over — your car still runs, just slower.
"""

CAR_NAME = "MyCarName"
CAR_COLOR = "#ff4400"

# Hardware specs — the physical limits your code operates within
ENGINE_SPEC = "v6_1000hp"
AERO_SPEC = "medium_downforce"
CHASSIS_SPEC = "standard"

# Legacy compat (required by current loader)
POWER = 20
GRIP = 20
WEIGHT = 20
AERO = 20
BRAKES = 20


# ═══════════════════════ POWERTRAIN ═══════════════════════

def engine_map(rpm, throttle_demand, engine_temp):
    """The engine's brain — how it responds to throttle.

    INPUTS:
      rpm: current engine RPM (4000-15000)
      throttle_demand: driver's throttle request (0.0-1.0)
      engine_temp: engine temperature in °C (80-130)

    RETURN: (torque_pct, fuel_flow_pct) — both 0.0-1.0
      torque_pct: how much of available torque to use
      fuel_flow_pct: how much fuel to flow (more fuel = more power)

    BAD CODE: Over-fuel and the engine overheats. Under-fuel and you lose power.
    """
    return (throttle_demand, throttle_demand)


def gearbox(rpm, speed, current_gear, throttle):
    """The transmission — when to shift.

    INPUTS:
      rpm: current engine RPM
      speed: car speed in km/h
      current_gear: current gear (1-8)
      throttle: current throttle position (0-1)

    RETURN: target_gear (1-8)

    BAD CODE: Shift too early = no power. Shift too late = engine damage.
    Peak torque at ~10,800 RPM. Peak power at ~12,500 RPM.
    """
    if rpm > 12000 and current_gear < 8:
        return current_gear + 1
    if rpm < 7000 and current_gear > 1:
        return current_gear - 1
    return current_gear


def fuel_mix(fuel_remaining_kg, laps_left, position, gap_ahead):
    """The fuel mixture valve — power vs conservation.

    INPUTS:
      fuel_remaining_kg: fuel left in kg
      laps_left: laps remaining
      position: race position (1 = first)
      gap_ahead: gap to car ahead in seconds

    RETURN: lambda_value (0.85-1.15)
      < 1.0 = rich (more power, burns more fuel)
      = 1.0 = stoichiometric (balanced)
      > 1.0 = lean (less power, saves fuel)

    BAD CODE: Run too rich and you run out of fuel. Run too lean and you lose.
    """
    if laps_left <= 0:
        return 1.0
    rate = fuel_remaining_kg / laps_left
    if rate > 2.2:
        return 0.92
    if rate < 1.6:
        return 1.10
    return 1.0


# ═══════════════════════ HYBRID SYSTEM ═══════════════════

def ers_deploy(battery_pct, speed, lap, gap_ahead, braking):
    """The battery — when to deploy stored energy.

    INPUTS:
      battery_pct: battery charge 0-100%
      speed: car speed km/h
      lap: current lap number
      gap_ahead: gap to car ahead in seconds
      braking: True if car is braking

    RETURN: deploy_kw (0-120)
      Higher = more power boost but drains battery faster.
      4 MJ deploy limit per lap.

    BAD CODE: Deplete battery before the overtaking zone.
    """
    if braking or battery_pct < 20:
        return 0
    return 80


def ers_harvest(braking_force, battery_pct, battery_temp):
    """The regeneration system — energy recovery under braking.

    INPUTS:
      braking_force: how hard the car is braking (0-1)
      battery_pct: current charge 0-100%
      battery_temp: battery temperature °C (25-60)

    RETURN: harvest_kw (0-120)
      Higher = more energy recovered but changes brake feel.
      2 MJ harvest limit per lap.

    BAD CODE: Battery overheats (>55°C) and ERS shuts down.
    """
    if battery_pct > 95 or battery_temp > 50:
        return 0
    return min(120, braking_force * 0.4)


# ═══════════════════════ CHASSIS ═════════════════════════

def suspension(speed, lateral_g, bump_severity, current_ride_height):
    """The ride height controller — ground effect vs safety.

    INPUTS:
      speed: car speed km/h
      lateral_g: cornering force in G
      bump_severity: track bumpiness (0-1)
      current_ride_height: current height (-1 to 1)

    RETURN: ride_height_target (-1.0 to 1.0)
      Lower = more ground effect downforce.
      Too low = bottoms out (sparks, bouncing, damage).

    BAD CODE: Bottom out on straights. Lose downforce in corners.
    """
    if speed > 250:
        return -0.5
    return -0.2


def brake_bias(speed, deceleration_g, tire_grip_front, tire_grip_rear):
    """The brake balance bar — front vs rear.

    INPUTS:
      speed: car speed km/h
      deceleration_g: braking force in G
      tire_grip_front: front tire grip (0-2)
      tire_grip_rear: rear tire grip (0-2)

    RETURN: front_pct (50-65)
      Higher = more front braking (stable but risk front lockup).
      Lower = more rear braking (sharper turn-in but risk spin).

    BAD CODE: Too much rear bias in heavy braking = spin.
    """
    return 57


def cooling(engine_temp, brake_temp, battery_temp, speed):
    """The cooling duct controller — drag vs temperature.

    INPUTS:
      engine_temp: engine °C (80-130, >120 = losing power)
      brake_temp: brake °C (200-1200, >800 = fade)
      battery_temp: battery °C (25-60, >55 = ERS shutdown)
      speed: car speed km/h

    RETURN: cooling_effort (0.0-1.0)
      Higher = better cooling but more aerodynamic drag.

    BAD CODE: Not enough cooling = overheat. Too much = slow from drag.
    """
    if engine_temp > 115 or battery_temp > 50:
        return 0.9
    return 0.4


def differential(corner_phase, speed, lateral_g):
    """The diff lock controller — traction vs rotation.

    INPUTS:
      corner_phase: "entry", "mid", "exit", or "straight"
      speed: car speed km/h
      lateral_g: cornering force in G

    RETURN: lock_pct (0-100)
      Higher = more traction but understeer.
      Lower = more rotation but wheelspin risk.

    BAD CODE: Over-lock in corners = can't turn. Under-lock on exit = wheelspin.
    """
    if corner_phase == "entry":
        return 40
    if corner_phase == "mid":
        return 25
    if corner_phase == "exit":
        return 70
    return 50


# ═══════════════════════ PIT WALL ════════════════════════

def strategy(state):
    """The pit wall radio — when to pit, what tires, what mode.

    INPUTS:
      state: full telemetry dict with ALL car data:
        speed, position, lap, total_laps, tire_wear, tire_compound,
        fuel_remaining, gap_ahead_s, gap_behind_s, safety_car,
        track_wetness, damage, ers_energy, brake_temp, engine_temp...

    RETURN: dict with strategic decisions:
      pit_request: bool — request a pit stop
      tire_compound_request: str — "soft"/"medium"/"hard"/"intermediate"/"wet"
      engine_mode: str — "push"/"standard"/"conserve"
      ers_deploy_mode: str — "attack"/"balanced"/"harvest"

    This is the team principal's job. Everything else is engineering.
    """
    if state.get("tire_wear", 0) > 0.7 and state.get("pit_stops", 0) == 0:
        return {"pit_request": True, "tire_compound_request": "hard"}
    return {"engine_mode": "standard"}
