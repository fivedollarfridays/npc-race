"""Sprint 16 integration gate — championship verification (T16.6)."""

import pathlib
import tempfile

import pytest

from engine.season_runner import run_season

pytestmark = pytest.mark.slow

CARS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "cars")


class TestSeasonEndToEnd:
    def test_short_season_completes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza", "monaco"],
                                laps=2, output_dir=tmpdir)
        assert len(result["races"]) == 2

    def test_standings_have_all_cars(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza"],
                                laps=2, output_dir=tmpdir)
        assert len(result["standings"]) >= 3

    def test_points_awarded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza"],
                                laps=2, output_dir=tmpdir)
        total_pts = sum(d["points"] for d in result["standings"].values())
        assert total_pts > 0

    def test_winner_has_most_points(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza", "monaco"],
                                laps=2, output_dir=tmpdir)
        from engine.championship import get_sorted_standings
        sorted_s = get_sorted_standings(result["standings"])
        assert sorted_s[0][1] >= sorted_s[-1][1]


class TestDevelopment:
    def test_dev_points_earned(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza"],
                                laps=2, output_dir=tmpdir)
        has_pts = any(ds["dev_points"] > 0 for ds in result["dev_states"].values())
        assert has_pts

    def test_car_stats_within_budget(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_season(car_dir=CARS_DIR, custom_tracks=["monza"],
                                laps=2, output_dir=tmpdir)
        for ds in result["dev_states"].values():
            total = sum(ds["base_stats"][s] + ds["upgrades"][s]
                         for s in ds["upgrades"])
            assert total <= 100


class TestArchCompliance:
    def test_simulation_unchanged(self):
        sim = pathlib.Path("engine/simulation.py").read_text()
        assert len(sim.splitlines()) <= 400
        assert sim.count("\n    def ") + sim.count("\ndef ") <= 15

    def test_new_modules_under_limits(self):
        limits = {
            "engine/season.py": 80,
            "engine/championship.py": 90,
            "engine/car_development.py": 100,
            "engine/season_runner.py": 120,
        }
        for path, limit in limits.items():
            lines = len(pathlib.Path(path).read_text().splitlines())
            assert lines <= limit, f"{path} has {lines} lines (limit: {limit})"
