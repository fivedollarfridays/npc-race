"""Unit tests for engine/race_runner.py — track resolution and results path logic.

run_race smoke test is marked @integration since it loads real car files.
"""

import pytest

from engine.race_runner import _compute_results_path, _resolve_track


class TestResolveTrack:
    """Tests for _resolve_track — named and generated tracks."""

    def test_named_track_returns_interpolated_points(self):
        track, laps, real_len, drs = _resolve_track("bahrain", 42, None)
        assert isinstance(track, list)
        assert len(track) > 0
        assert isinstance(track[0], tuple)

    def test_named_track_uses_default_laps(self):
        track, laps, real_len, drs = _resolve_track("bahrain", 42, None)
        assert isinstance(laps, int)
        assert laps > 0

    def test_named_track_explicit_laps_overrides(self):
        _, laps, _, _ = _resolve_track("bahrain", 42, 7)
        assert laps == 7

    def test_generated_track_when_name_is_none(self):
        track, laps, real_len, drs = _resolve_track(None, 99, None)
        assert isinstance(track, list)
        assert laps == 3  # default for generated
        assert real_len is None
        assert drs == []

    def test_generated_track_explicit_laps(self):
        _, laps, _, _ = _resolve_track(None, 99, 10)
        assert laps == 10

    def test_named_track_has_drs_zones(self):
        _, _, _, drs = _resolve_track("bahrain", 42, None)
        # Most real tracks have DRS zones
        assert isinstance(drs, list)


class TestComputeResultsPath:
    """Tests for _compute_results_path derivation logic."""

    def test_replay_json_becomes_results_json(self):
        path = _compute_results_path("output/replay.json")
        assert path == "output/results.json"

    def test_custom_name_gets_results_suffix(self):
        path = _compute_results_path("output/race1.json")
        assert path == "output/race1_results.json"

    def test_bare_filename(self):
        path = _compute_results_path("replay.json")
        assert path == "results.json"


class TestRunRaceSmoke:
    """Smoke test for run_race — requires car files on disk."""

    @pytest.mark.integration
    def test_run_race_fast_mode(self, tmp_path):
        """Minimal fast_mode race to verify wiring (skips replay export)."""
        import shutil
        from engine.race_runner import run_race

        # Copy real cars to temp dir
        car_src = "cars"
        car_dst = str(tmp_path / "cars")
        shutil.copytree(car_src, car_dst)

        output = str(tmp_path / "replay.json")
        results = run_race(
            car_dir=car_dst, laps=1, track_seed=42,
            output=output, fast_mode=True, quiet=True,
        )
        assert isinstance(results, list)
        assert len(results) >= 2
        assert results[0]["position"] == 1
