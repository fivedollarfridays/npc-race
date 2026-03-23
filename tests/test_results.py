"""Tests for engine.results — lightweight results summary."""

import json
from datetime import datetime

from engine.results import (
    compute_integrity_hash,
    generate_results_summary,
    verify_integrity,
)


def _make_replay():
    """Build a minimal replay dict matching the real replay structure."""
    return {
        "track_name": "monza",
        "laps": 5,
        "ticks_per_sec": 30,
        "frames": [
            [{"x": 0, "y": 0, "name": "CarA", "speed": 200}],
            [{"x": 1, "y": 1, "name": "CarA", "speed": 210}],
        ],
        "results": [
            {
                "name": "CarA",
                "position": 1,
                "total_time_s": 405.23,
                "best_lap_s": 80.12,
                "lap_times": [81.5, 80.8, 80.3, 80.12, 82.5],
                "finished": True,
                "color": "#ff0000",
                "finish_tick": 12157,
                "pit_stops": 1,
            },
            {
                "name": "CarB",
                "position": 2,
                "total_time_s": 408.50,
                "best_lap_s": 81.00,
                "lap_times": [82.0, 81.5, 81.0, 81.5, 82.5],
                "finished": True,
                "color": "#0000ff",
                "finish_tick": 12255,
                "pit_stops": 0,
            },
        ],
    }


def _make_cars():
    """Build minimal car dicts matching what run_race passes."""
    return [
        {
            "CAR_NAME": "CarA",
            "_loaded_parts": ["gearbox", "cooling", "strategy"],
            "reliability_score": 0.94,
        },
        {
            "CAR_NAME": "CarB",
            "_loaded_parts": ["gearbox"],
            "_source": "def engine_map(state, physics, hw): return 0.8\n",
        },
    ]


# --- Test 1: required top-level fields ---

def test_summary_has_required_fields():
    summary = generate_results_summary(_make_replay(), _make_cars(), league="F3")
    for key in ("version", "track", "laps", "league", "timestamp", "cars"):
        assert key in summary, f"Missing top-level key: {key}"


# --- Test 2: car entry fields ---

def test_summary_car_has_fields():
    summary = generate_results_summary(_make_replay(), _make_cars(), league="F3")
    required = {
        "name", "position", "total_time_s", "best_lap_s",
        "lap_times", "finished", "reliability_score", "league", "loaded_parts",
    }
    for car in summary["cars"]:
        missing = required - set(car.keys())
        assert not missing, f"Car {car.get('name')} missing fields: {missing}"


# --- Test 3: small size ---

def test_summary_small_size():
    summary = generate_results_summary(_make_replay(), _make_cars())
    raw = json.dumps(summary)
    assert len(raw) < 50_000, f"Summary too large: {len(raw)} bytes"


# --- Test 4: no frames key ---

def test_summary_no_frames():
    summary = generate_results_summary(_make_replay(), _make_cars())
    assert "frames" not in summary, "Summary must not contain 'frames'"


# --- Test 5: ISO 8601 timestamp ---

def test_summary_timestamp_format():
    summary = generate_results_summary(_make_replay(), _make_cars())
    ts = summary["timestamp"]
    # Must parse as ISO 8601
    parsed = datetime.fromisoformat(ts)
    assert isinstance(parsed, datetime)


# --- Test 6: real race integration ---

def test_summary_from_real_race():
    """Run a 1-lap race, generate summary, verify structure."""
    from tracks import get_track
    from engine.car_loader import load_all_cars
    from engine.track_gen import interpolate_track
    from engine.simulation import RaceSim

    track_data = get_track("monza")
    track = interpolate_track(track_data["control_points"], resolution=500)
    cars = load_all_cars("cars")
    assert len(cars) >= 2, "Need at least 2 seed cars"

    sim = RaceSim(
        cars, track, laps=1, seed=42,
        track_name="monza",
        real_length_m=track_data.get("real_length_m"),
    )
    sim.run()
    replay = sim.export_replay()

    summary = generate_results_summary(replay, cars, league="F3")

    assert summary["track"] == "monza"
    assert summary["laps"] == 1
    assert summary["league"] == "F3"
    assert len(summary["cars"]) == len(cars)

    for car_entry in summary["cars"]:
        assert car_entry["position"] >= 1
        assert isinstance(car_entry["finished"], bool)
        assert isinstance(car_entry["lap_times"], list)

    # Must be small
    raw = json.dumps(summary)
    assert len(raw) < 50_000
    assert "frames" not in summary


# --- Test 7: integrity hash present ---

def test_integrity_hash_present():
    summary = generate_results_summary(_make_replay(), _make_cars())
    assert "integrity" in summary
    assert summary["integrity"].startswith("sha256:")


# --- Test 8: integrity verifies ---

def test_integrity_verifies():
    summary = generate_results_summary(_make_replay(), _make_cars())
    assert verify_integrity(summary) is True


# --- Test 9: integrity fails on tamper ---

def test_integrity_fails_on_tamper():
    summary = generate_results_summary(_make_replay(), _make_cars())
    summary["cars"][0]["lap_times"][0] = 999.99
    assert verify_integrity(summary) is False


# --- Test 10: integrity ignores timestamp ---

def test_integrity_ignores_timestamp():
    summary = generate_results_summary(_make_replay(), _make_cars())
    original_hash = summary["integrity"]
    summary["timestamp"] = "2099-01-01T00:00:00+00:00"
    assert verify_integrity(summary) is True
    assert compute_integrity_hash(summary) == original_hash


# --- Test 11: hash deterministic ---

def test_hash_deterministic():
    replay = _make_replay()
    cars = _make_cars()
    s1 = generate_results_summary(replay, cars)
    s2 = generate_results_summary(replay, cars)
    # Remove timestamps so we compare the hash over same data
    s1.pop("timestamp")
    s2.pop("timestamp")
    assert compute_integrity_hash(s1) == compute_integrity_hash(s2)
