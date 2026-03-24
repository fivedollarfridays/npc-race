"""Tests for automatic results export alongside replay.

Integration tests (smoke-marked) verify run_race writes files.
Unit tests verify results structure via generate_results_summary directly.
"""

import json
import os
import tempfile

import pytest

from engine.results import generate_results_summary
from tests.fixtures.race_data import SAMPLE_RESULTS, SAMPLE_CARS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_replay_stub(
    results: list[dict] | None = None,
    track: str = "monza",
    laps: int = 1,
) -> dict:
    """Build a minimal replay-like dict for generate_results_summary."""
    return {
        "results": results or SAMPLE_RESULTS,
        "track_name": track,
        "laps": laps,
    }


def _run_race_to_tmpdir(output_name="replay.json"):
    """Run a minimal race into a temp directory, return (tmpdir, output_path)."""
    from engine.race_runner import run_race

    tmpdir = tempfile.mkdtemp()
    output = os.path.join(tmpdir, output_name)
    run_race(
        car_dir="cars",
        laps=1,
        track_name="monza",
        output=output,
    )
    return tmpdir, output


# --- Cycle 1: results file produced alongside replay (needs real sim) ---


@pytest.mark.smoke
def test_run_race_produces_results_file():
    """replay.json -> results.json in same directory."""
    tmpdir, _output = _run_race_to_tmpdir("replay.json")
    results_path = os.path.join(tmpdir, "results.json")
    assert os.path.exists(results_path), (
        f"Expected results.json at {results_path}"
    )


@pytest.mark.smoke
def test_custom_output_produces_results_file():
    """race_monza.json -> race_monza_results.json in same directory."""
    tmpdir, _output = _run_race_to_tmpdir("race_monza.json")
    results_path = os.path.join(tmpdir, "race_monza_results.json")
    assert os.path.exists(results_path), (
        f"Expected race_monza_results.json at {results_path}"
    )


# --- Cycle 2: results summary structure (unit, no sim needed) ---


def test_results_summary_is_dict():
    """generate_results_summary returns a dict."""
    replay = _build_replay_stub()
    data = generate_results_summary(replay, SAMPLE_CARS)
    assert isinstance(data, dict)


def test_results_has_required_fields():
    """Results must have version, track, laps, league, timestamp, cars."""
    replay = _build_replay_stub()
    data = generate_results_summary(replay, SAMPLE_CARS)
    for key in ("version", "track", "laps", "league", "timestamp", "cars"):
        assert key in data, f"Missing key: {key}"
    assert len(data["cars"]) >= 2


def test_results_cars_have_positions():
    """Each car entry should have name, position, and finished fields."""
    replay = _build_replay_stub()
    data = generate_results_summary(replay, SAMPLE_CARS)
    for car in data["cars"]:
        assert "name" in car
        assert "position" in car
        assert "finished" in car


# --- Cycle 3: results has integrity hash (unit, no sim needed) ---


def test_results_has_integrity():
    """Results summary must include an integrity hash."""
    replay = _build_replay_stub()
    data = generate_results_summary(replay, SAMPLE_CARS)
    assert "integrity" in data, "Results must include integrity hash"
    assert data["integrity"].startswith("sha256:"), "Hash must be sha256 prefixed"


# --- Cycle 4: replay still works as before (needs real sim) ---


@pytest.mark.smoke
def test_replay_still_exists():
    """The replay file must still be produced (not replaced by results)."""
    tmpdir, output = _run_race_to_tmpdir("replay.json")
    assert os.path.exists(output), "Replay file should still exist"
    with open(output) as f:
        replay = json.load(f)
    assert "frames" in replay, "Replay should still contain frames"
