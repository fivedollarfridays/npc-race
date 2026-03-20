"""Track performance weights — how each track values different car attributes.

Each track has a weight profile that determines how component choices affect
lap time. Power tracks reward top speed; technical tracks reward grip.
"""

# Weights sum to ~1.0 for each track. Higher weight = more important.
TRACK_WEIGHTS = {
    "monza":       {"top_speed": 0.35, "low_grip": 0.05, "high_grip": 0.20, "braking": 0.25, "tire_wear": 0.10, "fuel": 0.05},
    "monaco":      {"top_speed": 0.05, "low_grip": 0.40, "high_grip": 0.05, "braking": 0.30, "tire_wear": 0.15, "fuel": 0.05},
    "silverstone": {"top_speed": 0.15, "low_grip": 0.10, "high_grip": 0.35, "braking": 0.15, "tire_wear": 0.20, "fuel": 0.05},
    "spa":         {"top_speed": 0.25, "low_grip": 0.10, "high_grip": 0.30, "braking": 0.15, "tire_wear": 0.15, "fuel": 0.05},
    "bahrain":     {"top_speed": 0.20, "low_grip": 0.15, "high_grip": 0.20, "braking": 0.20, "tire_wear": 0.20, "fuel": 0.05},
    "singapore":   {"top_speed": 0.10, "low_grip": 0.35, "high_grip": 0.10, "braking": 0.25, "tire_wear": 0.15, "fuel": 0.05},
    "suzuka":      {"top_speed": 0.15, "low_grip": 0.10, "high_grip": 0.35, "braking": 0.15, "tire_wear": 0.20, "fuel": 0.05},
    "interlagos":  {"top_speed": 0.20, "low_grip": 0.15, "high_grip": 0.25, "braking": 0.20, "tire_wear": 0.15, "fuel": 0.05},
    "hungaroring": {"top_speed": 0.10, "low_grip": 0.30, "high_grip": 0.15, "braking": 0.20, "tire_wear": 0.20, "fuel": 0.05},
    "baku":        {"top_speed": 0.30, "low_grip": 0.20, "high_grip": 0.10, "braking": 0.25, "tire_wear": 0.10, "fuel": 0.05},
    "barcelona":   {"top_speed": 0.15, "low_grip": 0.15, "high_grip": 0.25, "braking": 0.15, "tire_wear": 0.25, "fuel": 0.05},
    "imola":       {"top_speed": 0.15, "low_grip": 0.15, "high_grip": 0.25, "braking": 0.20, "tire_wear": 0.20, "fuel": 0.05},
    "jeddah":      {"top_speed": 0.25, "low_grip": 0.10, "high_grip": 0.25, "braking": 0.20, "tire_wear": 0.15, "fuel": 0.05},
    "melbourne":   {"top_speed": 0.20, "low_grip": 0.20, "high_grip": 0.15, "braking": 0.20, "tire_wear": 0.20, "fuel": 0.05},
    "montreal":    {"top_speed": 0.25, "low_grip": 0.15, "high_grip": 0.15, "braking": 0.25, "tire_wear": 0.15, "fuel": 0.05},
    "austin":      {"top_speed": 0.15, "low_grip": 0.15, "high_grip": 0.25, "braking": 0.20, "tire_wear": 0.20, "fuel": 0.05},
    "lusail":      {"top_speed": 0.20, "low_grip": 0.10, "high_grip": 0.30, "braking": 0.15, "tire_wear": 0.20, "fuel": 0.05},
    "shanghai":    {"top_speed": 0.20, "low_grip": 0.15, "high_grip": 0.25, "braking": 0.20, "tire_wear": 0.15, "fuel": 0.05},
    "mugello":     {"top_speed": 0.15, "low_grip": 0.10, "high_grip": 0.35, "braking": 0.15, "tire_wear": 0.20, "fuel": 0.05},
    "zandvoort":   {"top_speed": 0.10, "low_grip": 0.20, "high_grip": 0.30, "braking": 0.15, "tire_wear": 0.20, "fuel": 0.05},
}

# Default for unknown tracks
_DEFAULT_WEIGHTS = {"top_speed": 0.20, "low_grip": 0.15, "high_grip": 0.20, "braking": 0.20, "tire_wear": 0.20, "fuel": 0.05}

# Reference values for normalization (baseline "average" car)
_REF = {"top_speed_kmh": 330, "low_speed_grip": 1.0, "high_speed_grip": 0.85,
        "braking_g": 5.0, "tire_wear_mult": 1.0, "fuel_kg_per_lap": 1.85}


def get_track_performance(attributes: dict, track_name: str) -> float:
    """Compute a car's lap time modifier for a specific track.

    Returns seconds offset from baseline: negative = faster, positive = slower.
    Range: roughly -2.0 to +2.0 seconds.
    """
    w = TRACK_WEIGHTS.get(track_name, _DEFAULT_WEIGHTS)
    score = 0.0
    # Top speed: faster = better (negative modifier)
    score += (attributes.get("top_speed_kmh", 330) - _REF["top_speed_kmh"]) * -0.08 * w["top_speed"]
    # Grip: higher = better
    score += (attributes.get("low_speed_grip", 1.0) - _REF["low_speed_grip"]) * -5.0 * w["low_grip"]
    score += (attributes.get("high_speed_grip", 0.85) - _REF["high_speed_grip"]) * -5.0 * w["high_grip"]
    # Braking: higher G = better
    score += (attributes.get("braking_g", 5.0) - _REF["braking_g"]) * -2.0 * w["braking"]
    # Tire wear: lower mult = better (less wear)
    score += (attributes.get("tire_wear_mult", 1.0) - _REF["tire_wear_mult"]) * 3.0 * w["tire_wear"]
    # Fuel: lower = better
    score += (attributes.get("fuel_kg_per_lap", 1.85) - _REF["fuel_kg_per_lap"]) * 2.0 * w["fuel"]
    return round(score, 3)
