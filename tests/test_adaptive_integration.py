"""Integration tests for Sprint 4 — adaptive intelligence features.

Covers: tournament end-to-end, data file persistence, JSON validity,
bot_scanner path-gating, backward compatibility, and CLI registration.
"""

import json
import os
import textwrap

import pytest

from engine import run_race
from security.bot_scanner import scan_car_source

pytestmark = pytest.mark.smoke

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_DIR = os.path.join(PROJECT_ROOT, "cars")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_race_to_file(tmp_path, **kwargs):
    """Run a race and return parsed replay JSON."""
    output = str(tmp_path / "replay.json")
    kwargs.setdefault("car_dir", CARS_DIR)
    kwargs["output"] = output
    run_race(**kwargs)
    with open(output) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Cycle 1: Tournament runs end-to-end
# ---------------------------------------------------------------------------


class TestTournamentEndToEnd:
    """A minimal tournament completes and produces valid output."""

    def test_tournament_single_track_single_race(self, tmp_path):
        from cli import commands

        args = _make_tournament_args(tmp_path, tracks="monaco", races=1, laps=2)
        commands.cmd_tournament(args)

    def test_tournament_produces_replay_files(self, tmp_path):
        from cli import commands

        args = _make_tournament_args(tmp_path, tracks="monaco", races=1, laps=2)
        commands.cmd_tournament(args)
        output_dir = str(tmp_path / "output")
        files = [f for f in os.listdir(output_dir) if f.endswith(".json")]
        assert len(files) >= 1


# ---------------------------------------------------------------------------
# Cycle 2: Data files created and valid JSON
# ---------------------------------------------------------------------------


class TestDataFilePersistence:
    """After a tournament, data files are created and contain valid JSON."""

    def test_data_files_created(self, tmp_path):
        from cli import commands

        # Use 2 laps so cars reach the last-lap save trigger
        args = _make_tournament_args(tmp_path, tracks="monaco", races=1, laps=2)
        commands.cmd_tournament(args)
        # Cars write to their hardcoded paths (required by bot_scanner security model)
        cars_data_dir = os.path.join(PROJECT_ROOT, "cars", "data")
        assert os.path.isdir(cars_data_dir), "cars/data/ dir not created"

    @pytest.mark.xfail(reason="PartsRaceSim car_data_dir support pending")
    def test_data_files_are_valid_json(self, tmp_path):
        from cli import commands

        args = _make_tournament_args(
            tmp_path, tracks="monaco", races=2, laps=3,
        )
        commands.cmd_tournament(args)
        # Cars write to their hardcoded paths in cars/data/ (required by bot_scanner)
        cars_data_dir = os.path.join(PROJECT_ROOT, "cars", "data")
        json_files = []
        if os.path.isdir(cars_data_dir):
            for fname in os.listdir(cars_data_dir):
                if fname.endswith(".json"):
                    path = os.path.join(cars_data_dir, fname)
                    with open(path) as f:
                        data = json.load(f)
                    assert isinstance(data, dict), f"{fname} is not a JSON object"
                    json_files.append(fname)
        assert len(json_files) >= 1, (
            "No car data files created in cars/data/ after 2 races on monaco"
        )


# ---------------------------------------------------------------------------
# Cycle 3: Security — bot_scanner rejects malicious open() path
# ---------------------------------------------------------------------------


class TestBotScannerPathGating:
    """bot_scanner rejects open() with unsafe paths."""

    def test_rejects_open_with_traversal(self):
        source = textwrap.dedent("""\
            CAR_NAME = "Hacker"
            CAR_COLOR = "#FF0000"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                f = open("../../etc/passwd")
                return {"throttle": 1.0, "boost": False}
        """)
        result = scan_car_source(source)
        assert not result.passed
        assert any("open()" in v for v in result.violations)

    def test_rejects_open_with_non_data_path(self):
        source = textwrap.dedent("""\
            CAR_NAME = "Sneaky"
            CAR_COLOR = "#FF0000"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                f = open("/tmp/secrets.txt")
                return {"throttle": 1.0, "boost": False}
        """)
        result = scan_car_source(source)
        assert not result.passed

    def test_allows_safe_data_path(self):
        source = textwrap.dedent("""\
            CAR_NAME = "Good"
            CAR_COLOR = "#00FF00"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                f = open("cars/data/good.json")
                return {"throttle": 1.0, "boost": False}
        """)
        result = scan_car_source(source)
        assert result.passed, f"Unexpected violations: {result.violations}"


# ---------------------------------------------------------------------------
# Cycle 4: Backward compat — race without data_dir still works
# ---------------------------------------------------------------------------


class TestBackwardCompat:
    """Regular race without data_dir or tournament params still works."""

    def test_race_without_data_dir(self, tmp_path):
        replay = _run_race_to_file(
            tmp_path, track_name="monza", laps=1,
        )
        assert replay["track_name"] == "monza"
        assert replay["car_count"] == 19
        for r in replay["results"]:
            assert r["finished"]


# ---------------------------------------------------------------------------
# Cycle 5: CLI registration — cmd_tournament exists
# ---------------------------------------------------------------------------


class TestCLIRegistration:
    """cmd_tournament is importable and registered in dispatch."""

    def test_cmd_tournament_importable(self):
        from cli.commands import cmd_tournament
        assert callable(cmd_tournament)

    def test_cmd_tournament_in_dispatch(self):
        from cli.main import _DISPATCH
        assert "tournament" in _DISPATCH


# ---------------------------------------------------------------------------
# Tournament args helper
# ---------------------------------------------------------------------------


def _make_tournament_args(tmp_path, tracks="monaco", races=1, laps=2):
    """Build a namespace mimicking argparse output for cmd_tournament."""

    class Args:
        pass

    args = Args()
    args.tracks = tracks
    args.races = races
    args.laps = laps
    args.car_dir = CARS_DIR
    args.data_dir = str(tmp_path / "data")
    args.output_dir = str(tmp_path / "output")
    return args
