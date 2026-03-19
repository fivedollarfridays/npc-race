"""Car damage model — accumulated damage affects performance."""

MAX_DAMAGE = 1.0
DNF_THRESHOLD = 0.8
PIT_REPAIR_AMOUNT = 0.3
PIT_REPAIR_EXTRA_TICKS = 90  # 3 extra seconds


def create_damage_state() -> dict:
    """Return initial damage state."""
    return {"damage": 0.0, "dnf": False}


def apply_damage(damage_state: dict, amount: float) -> dict:
    """Add damage. If above DNF threshold, mark DNF."""
    new_damage = min(MAX_DAMAGE, damage_state["damage"] + amount)
    dnf = new_damage >= DNF_THRESHOLD
    return {"damage": new_damage, "dnf": dnf}


def compute_damage_penalties(damage: float) -> dict:
    """Return performance multipliers based on damage level.

    Returns dict with:
      aero_mult:  1.0 at 0 damage -> 0.5 at max (linear)
      grip_mult:  1.0 at 0 damage -> 0.7 at max (linear)
      speed_mult: 1.0 at 0 damage -> 0.85 at max (linear)
    """
    d = min(MAX_DAMAGE, max(0.0, damage))
    return {
        "aero_mult": 1.0 - 0.5 * d,
        "grip_mult": 1.0 - 0.3 * d,
        "speed_mult": 1.0 - 0.15 * d,
    }


def repair_in_pit(damage_state: dict) -> tuple[dict, int]:
    """Repair damage during pit stop.

    Returns (updated_state, extra_ticks_for_repair).
    Only repairs if damage > 0.05.
    """
    if damage_state["damage"] <= 0.05:
        return damage_state.copy(), 0
    new_damage = max(0.0, damage_state["damage"] - PIT_REPAIR_AMOUNT)
    return {"damage": new_damage, "dnf": False}, PIT_REPAIR_EXTRA_TICKS
