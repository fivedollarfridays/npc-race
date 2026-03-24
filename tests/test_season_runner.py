"""Tests for season runner (T16.4)."""

import os
import tempfile

import pytest

from engine.season_runner import run_season

pytestmark = pytest.mark.smoke

CARS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars")


class TestRunSeason:
    def test_run_season_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, season_name="short",
                                laps=2, output_dir=tmpdir)
        assert isinstance(result, dict)
        assert "standings" in result
        assert "races" in result

    def test_season_runs_all_rounds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza", "monaco"],
                                laps=2, output_dir=tmpdir)
        assert len(result["races"]) == 2

    def test_standings_populated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza"],
                                laps=2, output_dir=tmpdir)
        assert len(result["standings"]) >= 3

    def test_dev_points_awarded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza"],
                                laps=2, output_dir=tmpdir)
        has_points = any(ds["dev_points"] > 0 for ds in result["dev_states"].values())
        assert has_points

    def test_output_dir_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outdir = os.path.join(tmpdir, "season")
            run_season(car_dir=CARS_DIR, custom_tracks=["monza"],
                       laps=2, output_dir=outdir)
        assert os.path.isdir(outdir)
        assert any(f.endswith(".json") for f in os.listdir(outdir))
