"""Lightweight results summary extracted from a full race replay.

Produces a small JSON-serializable dict (~10KB) vs the full replay (10MB+).
"""

import hashlib
import json

from datetime import datetime, timezone


def _build_car_entry(result: dict, car: dict | None, league: str) -> dict:
    """Build one car's summary entry from replay result and car dict."""
    loaded_parts: list[str] = []
    reliability_score: float = 1.0

    if car is not None:
        loaded_parts = list(car.get("_loaded_parts", []))
        reliability_score = car.get("reliability_score", 1.0)

    return {
        "name": result["name"],
        "position": result["position"],
        "total_time_s": result.get("total_time_s"),
        "best_lap_s": result.get("best_lap_s"),
        "lap_times": list(result.get("lap_times", [])),
        "finished": result["finished"],
        "reliability_score": reliability_score,
        "league": league,
        "loaded_parts": loaded_parts,
    }


def _match_car(result_name: str, cars: list[dict]) -> dict | None:
    """Find the car dict whose name matches a result entry."""
    for car in cars:
        name = car.get("CAR_NAME") or car.get("name", "")
        if name == result_name:
            return car
    return None


def generate_results_summary(
    replay: dict,
    cars: list[dict],
    league: str = "F3",
) -> dict:
    """Generate a lightweight results summary from a race replay.

    Returns a small JSON-serializable dict (~10KB vs 10MB+ replay).
    """
    results = replay.get("results", [])

    car_entries = []
    for result in results:
        car = _match_car(result["name"], cars)
        car_entries.append(_build_car_entry(result, car, league))

    summary = {
        "version": "1.0",
        "track": replay.get("track_name", "unknown"),
        "laps": replay.get("laps", 0),
        "league": league,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cars": car_entries,
    }
    summary["integrity"] = compute_integrity_hash(summary)
    return summary


def compute_integrity_hash(results: dict) -> str:
    """Compute SHA-256 hash over results data (excluding timestamp and hash)."""
    hashable = dict(results)
    hashable.pop("integrity", None)
    hashable.pop("timestamp", None)
    canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"


def verify_integrity(results: dict) -> bool:
    """Verify the integrity hash matches the results data."""
    stored = results.get("integrity", "")
    computed = compute_integrity_hash(results)
    return stored == computed
