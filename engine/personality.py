"""Code Circuit personality profiler — derive racing traits from race history.

Analyzes pit strategy, tire wear, weather performance, overtake/defend ratios,
qualifying vs race pace, and driving style to build personality profiles.
"""

from __future__ import annotations

from typing import Any

__all__ = ["profile_car"]

# --- Thresholds ---

_LOW_WEAR = 0.035
_HIGH_BRAKE_TEMP = 600.0
_HIGH_SLIPSTREAM = 0.25
_HIGH_DEFEND_RATIO = 0.6
_WET_RATIO_MIN = 0.2
_WET_GAIN_MIN = 1.5
_ONE_STOP_RATIO = 0.6
_GRID_LOSS_MIN = 2.0
_POSITION_GAIN_MIN = 3.0
_MIN_RACES_FOR_TRAITS = 1


def profile_car(name: str, race_history: list[dict[str, Any]]) -> dict[str, Any]:
    """Build personality profile from race history.

    Returns dict with keys: traits, variant_name, bio.
    """
    if not race_history:
        return {"traits": [], "variant_name": "Rookie", "bio": "A newcomer yet to turn a competitive lap."}

    agg = _aggregate(race_history)
    traits = _detect_traits(agg)
    variant = _variant_name(traits)
    bio = _generate_bio(traits)
    return {"traits": traits, "variant_name": variant, "bio": bio}


def _aggregate(history: list[dict[str, Any]]) -> dict[str, float]:
    n = len(history)
    avg_wear = sum(r.get("avg_tire_wear_rate", 0.05) for r in history) / n
    avg_brake = sum(r.get("avg_brake_temp", 400) for r in history) / n
    avg_slipstream = sum(r.get("slipstream_pct", 0.1) for r in history) / n
    total_overtakes = sum(r.get("overtakes", 0) for r in history)
    total_defends = sum(r.get("defends", 0) for r in history)
    defend_ratio = total_defends / max(total_overtakes + total_defends, 1)
    wet_races = [r for r in history if r.get("wet_ratio", 0) >= _WET_RATIO_MIN]
    avg_wet_gain = (sum(r.get("wet_position_gain", 0) for r in wet_races) / len(wet_races)) if wet_races else 0.0
    wet_race_pct = len(wet_races) / n
    one_stop_pct = sum(1 for r in history if r.get("pit_stops", 1) <= 1) / n
    avg_grid_delta = sum(r.get("position", 5) - r.get("grid", 5) for r in history) / n
    avg_position_gain = sum(r.get("grid", 5) - r.get("position", 5) for r in history) / n
    total_spins = sum(r.get("spins", 0) for r in history)
    total_dnfs = sum(1 for r in history if r.get("dnf", False))
    incident_rate = (total_spins + total_dnfs) / n

    return {
        "races": n, "avg_wear": avg_wear, "avg_brake": avg_brake,
        "avg_slipstream": avg_slipstream, "defend_ratio": defend_ratio,
        "avg_wet_gain": avg_wet_gain, "wet_race_pct": wet_race_pct,
        "one_stop_pct": one_stop_pct, "avg_grid_delta": avg_grid_delta,
        "avg_position_gain": avg_position_gain, "incident_rate": incident_rate,
    }


def _detect_traits(agg: dict[str, float]) -> list[str]:
    traits: list[str] = []
    if agg["avg_wear"] <= _LOW_WEAR:
        traits.append("conservative tire manager")
    if agg["avg_brake"] >= _HIGH_BRAKE_TEMP:
        traits.append("late braker")
    if agg["wet_race_pct"] > 0 and agg["avg_wet_gain"] >= _WET_GAIN_MIN:
        traits.append("rain specialist")
    if agg["one_stop_pct"] >= _ONE_STOP_RATIO:
        traits.append("one-stop hero")
    if agg["defend_ratio"] >= _HIGH_DEFEND_RATIO:
        traits.append("aggressive defender")
    if agg["avg_slipstream"] >= _HIGH_SLIPSTREAM:
        traits.append("slipstream hunter")
    if agg["avg_grid_delta"] >= _GRID_LOSS_MIN:
        traits.append("qualifying ace")
    if agg["avg_position_gain"] >= _POSITION_GAIN_MIN:
        traits.append("sunday driver")
    if agg["incident_rate"] == 0 and agg["races"] >= _MIN_RACES_FOR_TRAITS:
        traits.append("clean racer")
    return traits


_VARIANTS: dict[str, str] = {
    "rain specialist": "Wet Weather Ace",
    "conservative tire manager": "Marathon Runner",
    "late braker": "Hard Charger",
    "aggressive defender": "The Wall",
    "one-stop hero": "The Gambler",
    "slipstream hunter": "Tow Hawk",
    "qualifying ace": "Saturday Star",
    "sunday driver": "Race Day Hero",
    "clean racer": "Smooth Operator",
}

_DEFAULT_VARIANT = "All-Rounder"


def _variant_name(traits: list[str]) -> str:
    for trait in traits:
        if trait in _VARIANTS:
            return _VARIANTS[trait]
    return _DEFAULT_VARIANT


_BIO_TEMPLATES: dict[str, str] = {
    "conservative tire manager": "Patience on the pedals — saves rubber while others burn through it.",
    "late braker": "Brakes later than anyone dares, turning every corner into an overtake zone.",
    "rain specialist": "When the heavens open, this driver comes alive.",
    "one-stop hero": "One pit stop and pure pace — the minimalist's masterclass.",
    "aggressive defender": "The door is always closed. Good luck getting past.",
    "slipstream hunter": "Lives in the tow, waiting for the perfect moment to strike.",
    "qualifying ace": "Untouchable on a single lap, but the race tells a different story.",
    "sunday driver": "Starts quiet, finishes loud — the ultimate race-day climber.",
    "clean racer": "Smooth, precise, and incident-free — a textbook operator.",
}

_DEFAULT_BIO = "A racer still writing their story on the tarmac."


def _generate_bio(traits: list[str]) -> str:
    for trait in traits:
        if trait in _BIO_TEMPLATES:
            return _BIO_TEMPLATES[trait]
    return _DEFAULT_BIO
