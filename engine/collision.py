"""Collision detection and resolution between cars."""
import random

CONTACT_DISTANCE = 1.0     # sim units — must be overlapping
CONTACT_LATERAL = 0.10     # nearly identical lane position
CONTACT_COOLDOWN = 900     # 30 seconds between contacts for same pair

# Most contacts are wheel-to-wheel racing (no effect). Actual collisions are rare.
SEVERITY_WEIGHTS = [
    ("racing", 0.80, {"speed_loss": (0, 0), "damage": 0.0}),          # normal proximity
    ("minor", 0.12, {"speed_loss": (2, 5), "damage": 0.0}),           # light brush
    ("moderate", 0.05, {"speed_loss": (5, 10), "damage": 0.02}),      # real contact
    ("severe", 0.02, {"speed_loss": (10, 20), "damage": 0.05, "spin": True}),
    ("critical", 0.01, {"speed_loss": (0, 0), "damage": 0.5, "dnf": True}),
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
