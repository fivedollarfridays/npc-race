"""Car development — upgrade stats between races using earned dev points."""

DEV_POINTS_PER_POSITION = [10, 7, 5, 3, 2, 1, 1, 1, 1, 1]
UPGRADE_COST = 5
MAX_UPGRADE_PER_STAT = 10
STAT_BUDGET = 100
STAT_NAMES = ("POWER", "GRIP", "WEIGHT", "AERO", "BRAKES")


def create_dev_state(car: dict) -> dict:
    """Return initial development state for a car."""
    return {
        "name": car.get("CAR_NAME", "Unknown"),
        "dev_points": 0,
        "upgrades": {s: 0 for s in STAT_NAMES},
        "base_stats": {s: car.get(s, 20) for s in STAT_NAMES},
    }


def award_dev_points(dev_state: dict, position: int) -> dict:
    """Award dev points based on finishing position."""
    idx = position - 1
    pts = DEV_POINTS_PER_POSITION[idx] if 0 <= idx < len(DEV_POINTS_PER_POSITION) else 0
    dev_state["dev_points"] += pts
    return dev_state


def apply_upgrades(dev_state: dict, upgrades: dict[str, int]) -> dict:
    """Apply stat upgrades. Validates budget cap and per-stat limits."""
    total_cost = sum(v * UPGRADE_COST for v in upgrades.values())
    if total_cost > dev_state["dev_points"]:
        return dev_state  # insufficient points
    for stat, amount in upgrades.items():
        if stat not in STAT_NAMES:
            continue
        current = dev_state["upgrades"].get(stat, 0)
        capped = min(amount, MAX_UPGRADE_PER_STAT - current)
        # Check budget cap
        total_stats = sum(dev_state["base_stats"][s] + dev_state["upgrades"][s]
                          for s in STAT_NAMES) + capped
        if total_stats > STAT_BUDGET:
            capped = max(0, STAT_BUDGET - (total_stats - capped))
        dev_state["upgrades"][stat] = current + capped
        dev_state["dev_points"] -= capped * UPGRADE_COST
    return dev_state


def get_available_upgrades(dev_state: dict) -> dict:
    """Return max possible upgrade per stat given current points and limits."""
    affordable = dev_state["dev_points"] // UPGRADE_COST
    result = {}
    for stat in STAT_NAMES:
        headroom = MAX_UPGRADE_PER_STAT - dev_state["upgrades"].get(stat, 0)
        total = sum(dev_state["base_stats"][s] + dev_state["upgrades"][s] for s in STAT_NAMES)
        budget_room = STAT_BUDGET - total
        result[stat] = min(affordable, headroom, budget_room)
    return result


def apply_dev_to_car(car: dict, dev_state: dict) -> dict:
    """Return car dict with development upgrades applied to stats."""
    result = dict(car)
    for stat in STAT_NAMES:
        result[stat] = car.get(stat, 20) + dev_state["upgrades"].get(stat, 0)
    return result
