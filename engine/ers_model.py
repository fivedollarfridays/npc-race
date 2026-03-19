"""Energy Recovery System (ERS) model for NPC Race.

Simulates F1 MGU-K battery deploy/harvest. Battery has 4 MJ capacity
with per-lap deploy tracking. Deploy modes affect speed bonus and
drain rate. Braking harvests energy up to 2 MJ per lap.
"""

ERS_CAPACITY = 4.0  # MJ max battery
ERS_HARVEST_LIMIT = 2.0  # MJ max harvest per lap (F1 MGU-K limit)
ERS_DEPLOY_RATE: dict[str, float] = {
    "attack": 0.010,   # MJ/s (×dt per tick) — depletes ~2.7 MJ over a 270s race
    "balanced": 0.005,  # MJ/s — moderate drain
    "harvest": 0.0,     # no deploy
}
ERS_SPEED_BONUS: dict[str, float] = {
    "attack": 8.0,    # km/h top speed bonus
    "balanced": 4.0,
    "harvest": 0.0,
}
ERS_HARVEST_RATE = 0.02  # MJ per unit braking force per tick


def create_ers_state() -> dict:
    """Return initial ERS state with full battery and zero lap counters."""
    return {
        "energy": ERS_CAPACITY,
        "lap_deploy": 0.0,
        "lap_harvest": 0.0,
    }


def update_ers(
    ers_state: dict, deploy_mode: str, braking_force: float, dt: float
) -> dict:
    """Update ERS: deploy energy and harvest under braking.

    Deploys energy based on mode (drains battery). Harvests energy
    proportional to braking force, capped at ERS_HARVEST_LIMIT per lap
    and ERS_CAPACITY total.

    Returns a new state dict (does not mutate input).
    """
    energy = ers_state["energy"]
    lap_deploy = ers_state["lap_deploy"]
    lap_harvest = ers_state["lap_harvest"]

    # Deploy: drain battery if energy available
    drain = ERS_DEPLOY_RATE.get(deploy_mode, 0.0) * dt
    if energy > 0.0 and drain > 0.0:
        drain = min(drain, energy)
        energy -= drain
        lap_deploy += drain

    # Harvest: recover energy under braking
    if braking_force > 0.0 and lap_harvest < ERS_HARVEST_LIMIT:
        harvest = braking_force * ERS_HARVEST_RATE * dt
        harvest = min(harvest, ERS_HARVEST_LIMIT - lap_harvest)
        harvest = min(harvest, ERS_CAPACITY - energy)
        energy += harvest
        lap_harvest += harvest

    return {
        "energy": energy,
        "lap_deploy": lap_deploy,
        "lap_harvest": lap_harvest,
    }


def get_ers_speed_bonus(ers_state: dict, deploy_mode: str) -> float:
    """Return speed bonus from ERS deployment (0 if battery empty)."""
    if ers_state["energy"] <= 0.0:
        return 0.0
    return ERS_SPEED_BONUS.get(deploy_mode, 0.0)


def reset_ers_lap(ers_state: dict) -> dict:
    """Reset per-lap counters (deploy used, harvest collected).

    Energy carries over; only lap accounting resets.
    """
    return {
        "energy": ers_state["energy"],
        "lap_deploy": 0.0,
        "lap_harvest": 0.0,
    }
