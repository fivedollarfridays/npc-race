"""Tiered car loading for progressive difficulty."""

from engine.car_loader import load_all_cars

# Classification based on observed race performance
TIERS: dict[str, list[str]] = {
    "rookie": [
        "Tortoise", "RustBucket", "PaperWeight", "SteamRoller",
    ],
    "midfield": [
        "IronSide", "CrossWind", "FoxFire", "DriftKing",
        "Gambler", "Chameleon",
    ],
    "front": [
        "GlassCanon", "Berserker", "NightFury", "Vortex", "Phantom",
    ],
    "veterans": [
        "BrickHouse", "Silky", "GooseLoose", "SlipStream",
    ],
}

# Which tiers to include at each progression level
TIER_GROUPS: dict[str, list[str]] = {
    "rookie": ["rookie"],
    "midfield": ["rookie", "midfield"],
    "front": ["rookie", "midfield", "front"],
    "full": ["rookie", "midfield", "front", "veterans"],
}


def load_tier_cars(tier: str = "full", cars_dir: str = "cars") -> list[dict]:
    """Load cars for a specific tier level.

    Args:
        tier: "rookie", "midfield", "front", or "full"
        cars_dir: directory containing car files

    Returns:
        List of car dicts for the specified tier group

    Raises:
        ValueError: if tier is not a valid tier name
    """
    if tier not in TIER_GROUPS:
        raise ValueError(
            f"Invalid tier: {tier}. Use: {list(TIER_GROUPS.keys())}"
        )

    all_cars = load_all_cars(cars_dir)

    if tier == "full":
        return all_cars

    allowed_names: set[str] = set()
    for tier_name in TIER_GROUPS[tier]:
        allowed_names.update(TIERS[tier_name])

    # Keep tier cars + any unclassified cars (player-created projects)
    all_classified = set()
    for names in TIERS.values():
        all_classified.update(names)

    return [c for c in all_cars
            if c["CAR_NAME"] in allowed_names or c["CAR_NAME"] not in all_classified]


def get_tier_for_car(car_name: str) -> str | None:
    """Get which tier a car belongs to.

    Returns:
        Tier name ("rookie", "midfield", "front", "veterans") or None.
    """
    for tier_name, names in TIERS.items():
        if car_name in names:
            return tier_name
    return None
