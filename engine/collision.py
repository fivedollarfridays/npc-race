"""Collision detection and resolution between cars."""
import random

CONTACT_DISTANCE = 3.0
CONTACT_LATERAL = 0.25
CONTACT_COOLDOWN = 60  # ticks

# Severity weights: minor=50%, moderate=30%, severe=15%, critical=5%
SEVERITY_WEIGHTS = [
    ("minor", 0.50, {"speed_loss": (5, 15), "damage": 0.0}),
    ("moderate", 0.30, {"speed_loss": (10, 20), "damage": 0.05, "spin": True}),
    ("severe", 0.15, {"speed_loss": (15, 30), "damage": 0.15, "spin": True}),
    ("critical", 0.05, {"speed_loss": (0, 0), "damage": 1.0, "dnf": True}),
]


def is_contact(car_a: dict, car_b: dict) -> bool:
    """Check if two cars are in contact range."""
    if car_a.get("finished") or car_b.get("finished"):
        return False
    pit_a = car_a.get("pit_state", {}).get("status", "racing")
    pit_b = car_b.get("pit_state", {}).get("status", "racing")
    if pit_a != "racing" or pit_b != "racing":
        return False
    dist = abs(car_a["distance"] - car_b["distance"])
    lat = abs(car_a.get("lateral", 0) - car_b.get("lateral", 0))
    return dist < CONTACT_DISTANCE and lat < CONTACT_LATERAL


def check_collisions(car_states: list[dict], rng: random.Random) -> list[dict]:
    """Check all pairs for contact. Returns list of collision event dicts."""
    events = []
    n = len(car_states)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = car_states[i], car_states[j]
            if a.get("contact_cooldown", 0) > 0 or b.get("contact_cooldown", 0) > 0:
                continue
            if is_contact(a, b):
                event = resolve_collision(a, b, rng)
                events.append(event)
    return events


def resolve_collision(car_a: dict, car_b: dict, rng: random.Random) -> dict:
    """Determine collision severity and outcomes."""
    roll = rng.random()
    cumulative = 0.0
    for severity, weight, outcomes in SEVERITY_WEIGHTS:
        cumulative += weight
        if roll < cumulative:
            speed_lo, speed_hi = outcomes["speed_loss"]
            speed_loss = rng.uniform(speed_lo, speed_hi) if speed_hi > 0 else 0
            return {
                "car_a": car_a["name"],
                "car_b": car_b["name"],
                "severity": severity,
                "speed_loss": speed_loss,
                "damage": outcomes["damage"],
                "spin": outcomes.get("spin", False),
                "dnf": outcomes.get("dnf", False),
            }
    # Fallback: minor
    return {
        "car_a": car_a["name"], "car_b": car_b["name"],
        "severity": "minor", "speed_loss": 10.0, "damage": 0.0,
        "spin": False, "dnf": False,
    }
