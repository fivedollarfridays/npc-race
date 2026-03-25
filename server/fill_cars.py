"""Generate AI fill cars from the rival car pool."""
import os
import random

from engine.car_loader import load_all_cars

CARS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars"
)


def generate_fill_cars(
    count: int,
    exclude_names: list[str] | None = None,
    seed: int | None = None,
) -> list[dict]:
    """Load random rival cars as AI fill opponents.

    Args:
        count: Number of AI cars needed.
        exclude_names: Car names already in lobby (avoid duplicates).
        seed: Random seed for reproducible fills.

    Returns:
        List of car config dicts compatible with lobby format.
    """
    exclude = set(exclude_names or [])
    rng = random.Random(seed)

    all_cars = load_all_cars(CARS_DIR)

    available = [c for c in all_cars if c["CAR_NAME"] not in exclude]

    rng.shuffle(available)
    selected = available[:count]

    return [
        {
            "car_id": None,
            "player_id": "ai",
            "name": car["CAR_NAME"],
            "color": car["CAR_COLOR"],
            "source": None,
            "_car_dict": car,
        }
        for car in selected
    ]
