"""Powertrain physics — engine, gearbox, and fuel computations.

Your car parts (engine_map, gearbox, fuel_mix) decide HOW to run the powertrain.
This module computes WHAT HAPPENS physically when those decisions meet the real world.
"""

import math

# --- Constants ---

# Real F1-like ratios: keep engine in 10000-13000 RPM at race speeds
GEAR_RATIOS = [0, 4.40, 3.50, 2.85, 2.40, 2.05, 1.75, 1.50, 1.30]  # index 1-8
FINAL_DRIVE = 2.8
TIRE_RADIUS_M = 0.33
MAX_RPM = 15000
IDLE_RPM = 4000

_TWO_PI = 2 * math.pi


def torque_curve(rpm: float) -> float:
    """Normalized torque output (0-1) at given RPM. Peaks at ~10800."""
    if rpm < 4000:
        return 0.3
    if rpm < 10800:
        return 0.3 + 0.7 * (rpm - 4000) / 6800  # linear rise
    if rpm < 12500:
        return 1.0  # plateau
    if rpm < 15000:
        return 1.0 - 0.4 * (rpm - 12500) / 2500  # falloff
    return 0.6  # above max — over-rev


def compute_rpm(speed_kmh: float, gear: int) -> float:
    """Compute engine RPM from vehicle speed and gear."""
    if gear < 1 or gear > 8:
        return IDLE_RPM
    speed_ms = speed_kmh / 3.6
    wheel_rps = speed_ms / (_TWO_PI * TIRE_RADIUS_M)
    rpm = wheel_rps * GEAR_RATIOS[gear] * FINAL_DRIVE * 60
    return max(IDLE_RPM, min(MAX_RPM, rpm))


def compute_wheel_torque(
    torque_pct: float, rpm: float, gear: int, engine_spec: dict
) -> float:
    """Compute torque at wheels from player's engine_map output."""
    max_torque = engine_spec.get("torque_nm", 400)  # ICE 300 + MGU-K ~100 Nm
    actual_torque = max_torque * torque_curve(rpm) * torque_pct
    if gear < 1 or gear > 8:
        return 0
    return actual_torque * GEAR_RATIOS[gear] * FINAL_DRIVE


def compute_acceleration(
    wheel_torque: float, mass_kg: float, drag_force: float, rolling_resistance: float
) -> float:
    """Compute acceleration in m/s^2 from wheel torque."""
    force = wheel_torque / TIRE_RADIUS_M - drag_force - rolling_resistance
    return force / mass_kg


def compute_fuel_consumption(
    fuel_flow_pct: float, lambda_value: float, max_fuel_flow_kghr: float, dt: float
) -> float:
    """Compute fuel consumed in kg this tick. Rich burns more, lean less."""
    mixture_mult = 1.0
    if lambda_value < 1.0:
        mixture_mult = 1.0 + (1.0 - lambda_value) * 1.5  # rich burns more
    elif lambda_value > 1.0:
        mixture_mult = 1.0 - (lambda_value - 1.0) * 0.8  # lean saves
    flow = fuel_flow_pct * max_fuel_flow_kghr * mixture_mult
    return max(0, flow * dt / 3600)  # kg per tick


def compute_engine_temp(
    current_temp: float, torque_pct: float, rpm: float,
    cooling_effort: float, dt: float,
) -> float:
    """Update engine temp. Load heats, cooling cools."""
    heat = torque_pct * (rpm / 10000) * 1.2 * dt
    cool = cooling_effort * max(0, current_temp - 80) * 0.05 * dt
    return max(80, current_temp + heat - cool)


def compute_mixture_torque_mult(lambda_value: float) -> float:
    """Rich mixture gives more torque, lean gives less."""
    if lambda_value < 1.0:
        return 1.0 + (1.0 - lambda_value) * 0.2  # up to +3%
    if lambda_value > 1.0:
        return 1.0 - (lambda_value - 1.0) * 0.35  # up to -5%
    return 1.0


def compute_power_force(
    hp: float, torque_pct: float, rpm: float, speed_kmh: float,
    ers_deploy_kw: float, mixture_mult: float,
) -> float:
    """Compute force at wheels from power. F = P / v.

    This naturally produces correct top speed (where power = drag).
    At low speed, force is high (good acceleration).
    At high speed, force drops off (drag-limited).
    """
    speed_ms = max(3.0, speed_kmh / 3.6)  # floor at ~10 km/h to avoid infinity
    # ICE power: HP × torque_curve(rpm) × player's torque_pct × mixture
    ice_watts = hp * 745.7 * torque_curve(rpm) * torque_pct * mixture_mult
    # ERS adds power directly
    ers_watts = ers_deploy_kw * 1000
    total_watts = ice_watts + ers_watts
    # Force = Power / velocity
    return total_watts / speed_ms
