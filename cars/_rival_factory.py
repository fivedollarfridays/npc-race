"""Rival car factory — generates rival car dicts from archetype templates.

Each archetype defines base stats and a strategy personality.
Stat noise is applied via seeded RNG for deterministic generation.
"""

import random
from typing import Any, Callable

STAT_KEYS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]

ARCHETYPES: dict[str, dict[str, Any]] = {
    "frontrunner": {
        "base_stats": {"POWER": 36, "GRIP": 18, "WEIGHT": 12, "AERO": 19, "BRAKES": 15},
    },
    "midfield": {
        "base_stats": {"POWER": 21, "GRIP": 22, "WEIGHT": 18, "AERO": 20, "BRAKES": 19},
    },
    "backmarker": {
        "base_stats": {"POWER": 19, "GRIP": 14, "WEIGHT": 28, "AERO": 20, "BRAKES": 19},
    },
    "wildcard": {
        "base_stats": {"POWER": 30, "GRIP": 20, "WEIGHT": 15, "AERO": 22, "BRAKES": 13},
    },
}


def _apply_noise(
    base_stats: dict[str, int], rng: random.Random, sigma: float = 3.0,
) -> dict[str, int]:
    """Apply Gaussian noise to base stats, clamp, and normalize to sum=100."""
    noisy = {k: max(5, base_stats[k] + rng.gauss(0, sigma)) for k in STAT_KEYS}
    total = sum(noisy.values())
    scaled = {k: max(5, noisy[k] * 100.0 / total) for k in STAT_KEYS}
    rounded = {k: int(round(scaled[k])) for k in STAT_KEYS}
    remainder = 100 - sum(rounded.values())
    if remainder != 0:
        target = max(STAT_KEYS, key=lambda k: rounded[k])
        rounded[target] += remainder
    return rounded


def _frontrunner_strategy(
    aggression: float = 0.8, pit_threshold: float = 0.65,
) -> Callable[[dict], dict]:
    """Aggressive: push engine, 1-stop, boost early."""
    def strategy(state: dict) -> dict:
        decision: dict[str, Any] = {}
        decision["engine_mode"] = "push" if state.get("position", 1) > 1 else "standard"
        decision["tire_mode"] = "push"
        if state.get("tire_wear", 0) > pit_threshold:
            decision["pit_request"] = True
            decision["tire_compound_request"] = "hard"
        final_laps = state.get("lap", 0) >= state.get("total_laps", 5) - 2
        decision["boost"] = state.get("boost_available", False) and final_laps
        return decision
    return strategy


def _midfield_strategy(
    aggression: float = 0.5, pit_threshold: float = 0.70,
) -> Callable[[dict], dict]:
    """Balanced: standard engine, adaptive pitting."""
    def strategy(state: dict) -> dict:
        decision: dict[str, Any] = {}
        decision["engine_mode"] = "standard"
        decision["tire_mode"] = "balanced"
        if state.get("tire_wear", 0) > pit_threshold:
            decision["pit_request"] = True
            compound = "medium" if state.get("pit_stops", 0) == 0 else "hard"
            decision["tire_compound_request"] = compound
        final_lap = state.get("lap", 0) >= state.get("total_laps", 5) - 1
        decision["boost"] = state.get("boost_available", False) and final_lap
        return decision
    return strategy


def _backmarker_strategy(
    aggression: float = 0.3, pit_threshold: float = 0.75,
) -> Callable[[dict], dict]:
    """Conservative: conserve engine, late pitting."""
    def strategy(state: dict) -> dict:
        decision: dict[str, Any] = {}
        decision["engine_mode"] = "conserve"
        decision["tire_mode"] = "conserve"
        if state.get("tire_wear", 0) > pit_threshold:
            decision["pit_request"] = True
            decision["tire_compound_request"] = "hard"
        decision["boost"] = False
        return decision
    return strategy


def _wildcard_strategy(
    aggression: float = 0.6, pit_threshold: float = 0.60,
) -> Callable[[dict], dict]:
    """Unpredictable: mode depends on position and lap."""
    def strategy(state: dict) -> dict:
        decision: dict[str, Any] = {}
        lap = state.get("lap", 0)
        pos = state.get("position", 10)
        if lap % 3 == 0 or pos <= 3:
            decision["engine_mode"] = "push"
            decision["tire_mode"] = "push"
        else:
            decision["engine_mode"] = "standard"
            decision["tire_mode"] = "balanced"
        if state.get("tire_wear", 0) > pit_threshold:
            decision["pit_request"] = True
            decision["tire_compound_request"] = "soft" if pos > 10 else "medium"
        final_laps = lap >= state.get("total_laps", 5) - 2
        decision["boost"] = state.get("boost_available", False) and final_laps
        return decision
    return strategy


_STRATEGY_BUILDERS: dict[str, Callable[..., Callable[[dict], dict]]] = {
    "frontrunner": _frontrunner_strategy,
    "midfield": _midfield_strategy,
    "backmarker": _backmarker_strategy,
    "wildcard": _wildcard_strategy,
}


def generate_rival(
    archetype: str, name: str, color: str, seed: int = 42,
) -> dict[str, Any]:
    """Generate a rival car dict from archetype template with stat noise.

    Returns dict with: CAR_NAME, CAR_COLOR, POWER, GRIP, WEIGHT, AERO,
    BRAKES, strategy. Stats sum to exactly 100 after noise + normalization.
    """
    if archetype not in ARCHETYPES:
        raise ValueError(f"Unknown archetype: {archetype!r}")
    arch = ARCHETYPES[archetype]
    rng = random.Random(seed)
    stats = _apply_noise(arch["base_stats"], rng)
    # Build strategy with seeded personality variation
    builder = _STRATEGY_BUILDERS[archetype]
    aggression = 0.4 + rng.random() * 0.5  # 0.4-0.9
    pit_threshold = 0.55 + rng.random() * 0.25  # 0.55-0.80
    strategy_fn = builder(aggression=aggression, pit_threshold=pit_threshold)
    return {
        "CAR_NAME": name,
        "CAR_COLOR": color,
        **stats,
        "strategy": strategy_fn,
    }
