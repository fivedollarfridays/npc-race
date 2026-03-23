"""Tests for automatic results export alongside replay."""

import json
import os
import tempfile

from engine.race_runner import run_race


def _run_race_to_tmpdir(output_name="replay.json"):
    """Run a minimal race into a temp directory, return (tmpdir, output_path)."""
    tmpdir = tempfile.mkdtemp()
    output = os.path.join(tmpdir, output_name)
    run_race(
        car_dir="cars",
        laps=1,
        track_name="monza",
        output=output,
    )
    return tmpdir, output


# --- Cycle 1: results file produced alongside replay ---

def test_run_race_produces_results_file():
    """replay.json -> results.json in same directory."""
    tmpdir, _output = _run_race_to_tmpdir("replay.json")
    results_path = os.path.join(tmpdir, "results.json")
    assert os.path.exists(results_path), (
        f"Expected results.json at {results_path}"
    )


def test_custom_output_produces_results_file():
    """race_monza.json -> race_monza_results.json in same directory."""
    tmpdir, _output = _run_race_to_tmpdir("race_monza.json")
    results_path = os.path.join(tmpdir, "race_monza_results.json")
    assert os.path.exists(results_path), (
        f"Expected race_monza_results.json at {results_path}"
    )


# --- Cycle 2: results file is valid JSON with expected structure ---

def test_results_file_is_valid_json():
    """The results file must be parseable JSON with dict structure."""
    tmpdir, _ = _run_race_to_tmpdir("replay.json")
    results_path = os.path.join(tmpdir, "results.json")
    with open(results_path) as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_results_has_required_fields():
    """Results must have version, track, laps, league, timestamp, cars."""
    tmpdir, _ = _run_race_to_tmpdir("replay.json")
    results_path = os.path.join(tmpdir, "results.json")
    with open(results_path) as f:
        data = json.load(f)
    for key in ("version", "track", "laps", "league", "timestamp", "cars"):
        assert key in data, f"Missing key: {key}"
    assert len(data["cars"]) >= 2


def test_results_cars_have_positions():
    """Each car entry should have name, position, and finished fields."""
    tmpdir, _ = _run_race_to_tmpdir("replay.json")
    results_path = os.path.join(tmpdir, "results.json")
    with open(results_path) as f:
        data = json.load(f)
    for car in data["cars"]:
        assert "name" in car
        assert "position" in car
        assert "finished" in car


# --- Cycle 3: results has integrity hash ---

def test_results_has_integrity():
    """Results file must include an integrity hash."""
    tmpdir, _ = _run_race_to_tmpdir("replay.json")
    results_path = os.path.join(tmpdir, "results.json")
    with open(results_path) as f:
        data = json.load(f)
    assert "integrity" in data, "Results must include integrity hash"
    assert data["integrity"].startswith("sha256:"), "Hash must be sha256 prefixed"


# --- Cycle 4: replay still works as before ---

def test_replay_still_exists():
    """The replay file must still be produced (not replaced by results)."""
    tmpdir, output = _run_race_to_tmpdir("replay.json")
    assert os.path.exists(output), "Replay file should still exist"
    with open(output) as f:
        replay = json.load(f)
    assert "frames" in replay, "Replay should still contain frames"
