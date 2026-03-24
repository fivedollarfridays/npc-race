"""Integration tests for NPC Race end-to-end pipeline.

Tests verify the full pipeline: load cars -> select track -> run race -> valid
replay JSON.
"""

import json
import os
import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.smoke

from engine import run_race, load_car, load_all_cars
from security.bot_scanner import scan_car_file, scan_car_source
from tracks import get_track, list_tracks, random_track, TRACKS

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_DIR = os.path.join(PROJECT_ROOT, "cars")

REPLAY_REQUIRED_KEYS = {
    "track", "track_width", "track_name", "laps",
    "ticks_per_sec", "frames", "results", "car_count",
}


# -- Helpers ----------------------------------------------------------


def _run_race_to_file(tmp_path, **kwargs):
    """Run a race and return the parsed replay JSON."""
    output = str(tmp_path / "replay.json")
    kwargs.setdefault("car_dir", CARS_DIR)
    kwargs["output"] = output
    run_race(**kwargs)
    with open(output) as f:
        return json.load(f)


# -- Test: Named track race ------------------------------------------


class TestNamedTrackRace:
    """Run a race on a named track and verify replay structure."""

    def test_replay_has_correct_track_name(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=1)
        assert replay["track_name"] == "monza"

    def test_replay_has_cars(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=1)
        assert replay["car_count"] >= 5  # at least the 5 seed cars
        assert len(replay["results"]) == replay["car_count"]

    def test_replay_schema_complete(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=1)
        missing = REPLAY_REQUIRED_KEYS - set(replay.keys())
        assert not missing, f"Missing replay keys: {missing}"


# -- Test: Procedural track backward compat ---------------------------


class TestProceduralTrack:
    """Procedural (seed-based) track still works when no track_name given."""

    def test_procedural_race_produces_valid_replay(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_seed=99, laps=1)
        assert replay["track_name"] is None
        missing = REPLAY_REQUIRED_KEYS - set(replay.keys())
        assert not missing, f"Missing replay keys: {missing}"

    def test_procedural_default_laps(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_seed=99)
        assert replay["laps"] == 3


# -- Test: All seed cars finish ---------------------------------------


class TestAllSeedCarsFinish:
    """All 5 shipped seed cars complete a 1-lap race."""

    def test_all_cars_finish(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="silverstone", laps=1)
        for result in replay["results"]:
            assert result["finished"], (
                f"{result['name']} did not finish"
            )

    def test_seed_cars_loaded(self):
        cars = load_all_cars(CARS_DIR)
        assert len(cars) >= 5  # 5 seed cars + default_project


# -- Test: Replay JSON schema detail ----------------------------------


class TestReplaySchema:
    """Verify replay JSON fields have correct types and structure."""

    def test_track_is_list_of_xy(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="spa", laps=1)
        assert isinstance(replay["track"], list)
        assert len(replay["track"]) > 0
        point = replay["track"][0]
        assert "x" in point and "y" in point

    def test_results_have_position_and_finish(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="spa", laps=1)
        for r in replay["results"]:
            assert "position" in r
            assert "finished" in r
            assert "name" in r
            assert "finish_tick" in r

    def test_frames_are_nonempty(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="spa", laps=1)
        assert len(replay["frames"]) > 0


# -- Test: Car validation rejects bad files ----------------------------


class TestCarValidation:
    """Bad car files are rejected by load_car or bot_scanner."""

    def test_missing_stats_rejected(self, tmp_path):
        bad_car = tmp_path / "bad.py"
        bad_car.write_text('CAR_NAME = "Bad"\nCAR_COLOR = "#FF0000"\n')
        with pytest.raises(ValueError, match="missing"):
            load_car(str(bad_car))

    def test_over_budget_rejected(self, tmp_path):
        bad_car = tmp_path / "rich.py"
        bad_car.write_text(textwrap.dedent("""\
            CAR_NAME = "Rich"
            CAR_COLOR = "#FF0000"
            POWER = 30
            GRIP = 30
            WEIGHT = 30
            AERO = 30
            BRAKES = 30
        """))
        with pytest.raises(ValueError, match="budget"):
            load_car(str(bad_car))


# -- Test: Malicious car file caught -----------------------------------


class TestMaliciousCarCaught:
    """Bot scanner catches import os and other violations."""

    def test_import_os_rejected(self):
        source = textwrap.dedent("""\
            import os
            CAR_NAME = "Hack"
            CAR_COLOR = "#FF0000"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(source)
        assert not result.passed
        assert any("os" in v for v in result.violations)

    def test_eval_call_rejected(self):
        source = textwrap.dedent("""\
            CAR_NAME = "Eviler"
            CAR_COLOR = "#FF0000"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                eval("print('hacked')")
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(source)
        assert not result.passed


# -- Test: Track selection ---------------------------------------------


class TestTrackSelection:
    """Verify track helper functions work correctly."""

    def test_get_track_returns_valid_data(self):
        track = get_track("monza")
        assert "control_points" in track
        assert "country" in track
        assert "laps_default" in track

    def test_get_track_unknown_raises(self):
        with pytest.raises(KeyError):
            get_track("nonexistent_track_xyz")

    def test_random_track_returns_valid_key(self):
        key = random_track()
        assert key in TRACKS

    def test_list_tracks_returns_all_20(self):
        names = list_tracks()
        assert len(names) == 20


# -- Test: CLI --list-tracks -------------------------------------------


class TestCLI:
    """CLI commands produce expected output."""

    def test_list_tracks_cli(self):
        result = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "play.py"),
             "--list-tracks"],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert "monza" in result.stdout
        assert "20 tracks" in result.stdout

    def test_track_flag_produces_replay(self, tmp_path):
        output = str(tmp_path / "cli_replay.json")
        result = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "play.py"),
             "--track", "monza", "--laps", "1",
             "--output", output, "--no-browser"],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        with open(output) as f:
            replay = json.load(f)
        assert replay["track_name"] == "monza"


# -- Test: End-to-end pipeline ----------------------------------------


class TestEndToEnd:
    """Full pipeline: init cars dir -> validate -> run race -> check replay."""

    def test_full_pipeline(self, tmp_path):
        # Step 1: Create a minimal valid car in a temp dir
        car_dir = tmp_path / "my_cars"
        car_dir.mkdir()

        car_a = car_dir / "racer_a.py"
        car_a.write_text(textwrap.dedent("""\
            CAR_NAME = "Racer A"
            CAR_COLOR = "#11AA22"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """))

        car_b = car_dir / "racer_b.py"
        car_b.write_text(textwrap.dedent("""\
            CAR_NAME = "Racer B"
            CAR_COLOR = "#BB3344"
            POWER = 25
            GRIP = 25
            WEIGHT = 15
            AERO = 20
            BRAKES = 15
            def strategy(state):
                return {"throttle": 0.9, "boost": False, "tire_mode": "push"}
        """))

        # Step 2: Validate both cars
        result_a = scan_car_file(str(car_a))
        result_b = scan_car_file(str(car_b))
        assert result_a.passed, f"Car A failed: {result_a.violations}"
        assert result_b.passed, f"Car B failed: {result_b.violations}"

        # Step 3: Run a race
        output = str(tmp_path / "e2e_replay.json")
        run_race(
            car_dir=str(car_dir),
            laps=1,
            track_name="bahrain",
            output=output,
        )

        # Step 4: Verify replay
        with open(output) as f:
            replay = json.load(f)

        assert replay["track_name"] == "bahrain"
        assert replay["car_count"] == 2
        assert len(replay["results"]) == 2
        missing = REPLAY_REQUIRED_KEYS - set(replay.keys())
        assert not missing, f"Missing: {missing}"

        # Step 5: Both cars finished
        for r in replay["results"]:
            assert r["finished"], f"{r['name']} DNF"
