"""Hybrid physics — ERS battery, differential, and tire load/grip.

Physics layer for player-coded parts: ers_deploy, ers_harvest, differential.
The player manages the hybrid system; physics determines whether they have
energy when they need it.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ERS constants (F1 2024 regulations)
# ---------------------------------------------------------------------------

ERS_CAPACITY_MJ: float = 4.0
ERS_MAX_DEPLOY_KW: float = 120.0
ERS_MAX_HARVEST_KW: float = 120.0
ERS_DEPLOY_LIMIT_MJ_PER_LAP: float = 4.0
ERS_HARVEST_LIMIT_MJ_PER_LAP: float = 2.0


def create_ers_state() -> dict:
    """Fresh ERS state with full battery."""
    return {
        "energy_mj": ERS_CAPACITY_MJ,
        "lap_deploy_mj": 0.0,
        "lap_harvest_mj": 0.0,
        "battery_temp": 30.0,
    }


def update_ers(
    ers_state: dict, deploy_kw: float, harvest_kw: float, dt: float,
) -> tuple[dict, float]:
    """Apply deploy and harvest. Returns (updated_state, actual_deploy_kw)."""
    # Deploy: drain battery (kW * s = kJ, /1000 = MJ)
    deploy_mj = deploy_kw * dt / 1000.0
    available = min(
        deploy_mj,
        ers_state["energy_mj"],
        ERS_DEPLOY_LIMIT_MJ_PER_LAP - ers_state["lap_deploy_mj"],
    )
    available = max(0.0, available)
    actual_deploy_kw = available / max(dt / 1000.0, 0.0001)

    # Harvest: charge battery
    harvest_mj = harvest_kw * dt / 1000.0
    can_harvest = min(
        harvest_mj,
        ERS_CAPACITY_MJ - ers_state["energy_mj"] + available,  # account for deploy drain
        ERS_HARVEST_LIMIT_MJ_PER_LAP - ers_state["lap_harvest_mj"],
    )
    can_harvest = max(0.0, can_harvest)

    new_energy = ers_state["energy_mj"] - available + can_harvest
    new_energy = max(0.0, min(ERS_CAPACITY_MJ, new_energy))

    # Battery temp: deploy and harvest both generate heat
    temp = ers_state["battery_temp"]
    temp_change = (
        (actual_deploy_kw + harvest_kw) * 0.0005 * dt
        - (temp - 30.0) * 0.01 * dt
    )

    return {
        "energy_mj": new_energy,
        "lap_deploy_mj": ers_state["lap_deploy_mj"] + available,
        "lap_harvest_mj": ers_state["lap_harvest_mj"] + can_harvest,
        "battery_temp": max(25.0, temp + temp_change),
    }, actual_deploy_kw


def reset_ers_lap(ers_state: dict) -> dict:
    """Reset per-lap counters on new lap."""
    return {**ers_state, "lap_deploy_mj": 0.0, "lap_harvest_mj": 0.0}


# ---------------------------------------------------------------------------
# Differential
# ---------------------------------------------------------------------------

def compute_diff_effect(
    lock_pct: float, lateral_g: float, speed_kmh: float,
) -> tuple[float, float]:
    """Differential effect on traction and handling.

    Returns (traction_mult, understeer_factor).
    Traction peaks at a speed-dependent optimal lock. Too high or too low costs grip.
    Slow corners want lower lock (rotation). Fast sweepers want higher lock (stability).
    """
    lock = lock_pct / 100.0
    # Optimal lock varies with speed: 0.2 at 0 km/h, 0.7 at 250+ km/h
    optimal_lock = min(0.9, 0.2 + speed_kmh / 500)
    lock_excess = max(0, lock - optimal_lock)
    lock_deficit = max(0, optimal_lock - lock)
    # Traction peaks at optimal, drops on either side
    traction = 1.0 - lock_deficit * 0.30 - lock_excess * 0.25
    traction = max(0.80, traction)
    understeer = lock * lateral_g * 0.1
    return traction, understeer


def compute_diff_tire_wear(
    lock_pct: float, lateral_g: float, dt: float,
) -> float:
    """Higher lock in corners = more inside tire wear."""
    lock = lock_pct / 100.0
    return lock * lateral_g * 0.0001 * dt


# ---------------------------------------------------------------------------
# Tire interaction
# ---------------------------------------------------------------------------

def compute_tire_load(
    mass_kg: float, downforce_n: float, lateral_g: float,
) -> float:
    """Total tire load from weight + downforce."""
    weight = mass_kg * 9.81
    return weight + downforce_n


def compute_grip_from_load(tire_load: float, tire_grip_base: float) -> float:
    """Grip scales with load but with diminishing returns (load sensitivity)."""
    normalized = tire_load / 8000.0  # reference load
    return tire_grip_base * (normalized ** 0.8)
