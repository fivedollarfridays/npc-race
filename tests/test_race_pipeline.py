"""Integration tests for qualifying + race pipeline (T34.8).

Tests CLI qualify/race commands, grid integration in run_race,
and the full qualify-to-race pipeline.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.track_gen import generate_track, interpolate_track


def _default_strategy(s):
    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}


def _make_car(name, power=20, strategy=None):
    strat = strategy or _default_strategy
    return {
        "CAR_NAME": name, "CAR_COLOR": "#FF0000",
        "POWER": power, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
        "strategy": strat,
    }


def _make_track():
    control = generate_track(seed=42)
    return interpolate_track(control, resolution=500)


def _write_car_file(directory, name, power=20):
    """Write a minimal car .py file into directory."""
    path = os.path.join(directory, f"{name}.py")
    other = (100 - power) // 4
    with open(path, "w") as f:
        f.write(f'''CAR_NAME = "{name}"
CAR_COLOR = "#FF0000"
POWER = {power}
GRIP = {other}
WEIGHT = {other}
AERO = {other}
BRAKES = {other}

def strategy(state):
    return {{"throttle": 1.0, "boost": False, "tire_mode": "balanced"}}
''')
    return path


# ── Cycle 1: cmd_qualify produces grid.json ──────────────────────────────


class TestCmdQualify:
    """npcrace qualify produces grid.json with all cars sorted by time."""

    def test_qualify_produces_grid_file(self):
        from cli.race_commands import cmd_qualify
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_car_file(tmpdir, "CarA", power=20)
            _write_car_file(tmpdir, "CarB", power=25)
            grid_path = os.path.join(tmpdir, "grid.json")

            args = _make_qualify_args(car_dir=tmpdir, track="monza",
                                      output=grid_path)
            cmd_qualify(args)

            assert os.path.isfile(grid_path)

    def test_grid_json_has_all_cars_sorted(self):
        from cli.race_commands import cmd_qualify
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_car_file(tmpdir, "CarA", power=15)
            _write_car_file(tmpdir, "CarB", power=30)
            grid_path = os.path.join(tmpdir, "grid.json")

            args = _make_qualify_args(car_dir=tmpdir, track="monza",
                                      output=grid_path)
            cmd_qualify(args)

            with open(grid_path) as f:
                grid = json.load(f)
            assert len(grid) == 2
            # Grid positions must be sequential
            positions = [r["grid_position"] for r in grid]
            assert positions == [1, 2]
            # Times must be sorted ascending
            times = [r["qualifying_time"] for r in grid]
            assert times == sorted(times)

    def test_qualify_prints_results(self, capsys):
        from cli.race_commands import cmd_qualify
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_car_file(tmpdir, "Solo", power=20)
            grid_path = os.path.join(tmpdir, "grid.json")

            args = _make_qualify_args(car_dir=tmpdir, track="monza",
                                      output=grid_path)
            cmd_qualify(args)

            captured = capsys.readouterr()
            assert "P1" in captured.out
            assert "Solo" in captured.out


# ── Cycle 2: Grid reordering in run_race ─────────────────────────────────


class TestGridIntegration:
    """run_race with grid_file reorders starting positions."""

    def test_run_race_accepts_grid_file(self):
        """run_race doesn't crash when given a grid_file parameter."""
        from engine.race_runner import run_race
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_car_file(tmpdir, "CarA")
            _write_car_file(tmpdir, "CarB")
            grid_path = os.path.join(tmpdir, "grid.json")
            grid = [
                {"name": "CarB", "qualifying_time": 80.0, "grid_position": 1},
                {"name": "CarA", "qualifying_time": 81.0, "grid_position": 2},
            ]
            with open(grid_path, "w") as f:
                json.dump(grid, f)

            output = os.path.join(tmpdir, "replay.json")
            results = run_race(
                car_dir=tmpdir, laps=1, track_name="monza",
                output=output, fast_mode=True, grid_file=grid_path,
            )
            assert isinstance(results, list)
            assert len(results) == 2


# ── Cycle 3: cmd_race --qualify pipeline ─────────────────────────────────


class TestCmdRace:
    """npcrace race --qualify runs the full pipeline."""

    def test_race_with_qualify_flag(self):
        from cli.race_commands import cmd_race
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_car_file(tmpdir, "CarA", power=20)
            _write_car_file(tmpdir, "CarB", power=25)
            output = os.path.join(tmpdir, "replay.json")

            args = _make_race_args(
                car_dir=tmpdir, track="monza", laps=1,
                qualify=True, output=output, no_browser=True,
            )
            cmd_race(args)

            # Grid file should have been created
            grid_path = os.path.join(tmpdir, "grid.json")
            assert os.path.isfile(grid_path)

            # Results should exist
            results_path = os.path.join(tmpdir, "results.json")
            assert os.path.isfile(results_path)

    def test_race_without_qualify_flag(self):
        from cli.race_commands import cmd_race
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_car_file(tmpdir, "CarA")
            _write_car_file(tmpdir, "CarB")
            output = os.path.join(tmpdir, "replay.json")

            args = _make_race_args(
                car_dir=tmpdir, track="monza", laps=1,
                qualify=False, output=output, no_browser=True,
            )
            cmd_race(args)

            # No grid file created when --qualify not passed
            grid_path = os.path.join(tmpdir, "grid.json")
            assert not os.path.isfile(grid_path)


# ── Cycle 4: P1 starts at front ──────────────────────────────────────────


class TestGridOrdering:
    """Qualifying P1 starts at front of race grid."""

    def test_p1_starts_at_front(self):
        """The car with grid_position=1 should start at distance 0."""
        from engine.race_runner import _reorder_by_grid
        cars = [
            {"CAR_NAME": "Back"},
            {"CAR_NAME": "Front"},
        ]
        grid = [
            {"name": "Front", "qualifying_time": 80.0, "grid_position": 1},
            {"name": "Back", "qualifying_time": 85.0, "grid_position": 2},
        ]
        reordered = _reorder_by_grid(cars, grid)
        assert reordered[0]["CAR_NAME"] == "Front"
        assert reordered[0].get("_grid_offset", 0) == 0

    def test_last_car_has_negative_offset(self):
        from engine.race_runner import _reorder_by_grid
        cars = [
            {"CAR_NAME": "A"},
            {"CAR_NAME": "B"},
            {"CAR_NAME": "C"},
        ]
        grid = [
            {"name": "B", "qualifying_time": 80.0, "grid_position": 1},
            {"name": "C", "qualifying_time": 81.0, "grid_position": 2},
            {"name": "A", "qualifying_time": 82.0, "grid_position": 3},
        ]
        reordered = _reorder_by_grid(cars, grid)
        assert reordered[0]["CAR_NAME"] == "B"
        assert reordered[2]["CAR_NAME"] == "A"
        # P3 should have offset -(3-1)*15 = -30
        assert reordered[2].get("_grid_offset", 0) == -30


# ── Cycle 5: CLI parser wiring ────────────────────────────────────────────


class TestCLIParser:
    """npcrace qualify and race subcommands parse correctly."""

    def test_qualify_parser(self):
        from cli.main import _build_parser
        parser = _build_parser()
        args = parser.parse_args(["qualify", "--track", "monza",
                                   "--car-dir", "mycars",
                                   "--output", "out.json"])
        assert args.command == "qualify"
        assert args.track == "monza"
        assert args.car_dir == "mycars"
        assert args.output == "out.json"

    def test_race_parser_with_qualify(self):
        from cli.main import _build_parser
        parser = _build_parser()
        args = parser.parse_args(["race", "--track", "monza", "--qualify",
                                   "--laps", "3", "--no-browser"])
        assert args.command == "race"
        assert args.qualify is True
        assert args.laps == 3
        assert args.no_browser is True

    def test_race_parser_defaults(self):
        from cli.main import _build_parser
        parser = _build_parser()
        args = parser.parse_args(["race"])
        assert args.qualify is False
        assert args.output == "replay.json"


# ── Helpers ───────────────────────────────────────────────────────────────


def _make_qualify_args(car_dir="cars", track="monza", output="grid.json"):
    """Build a namespace mimicking argparse for cmd_qualify."""

    class Args:
        pass

    a = Args()
    a.car_dir = car_dir
    a.track = track
    a.output = output
    return a


def _make_race_args(
    car_dir="cars", track="monza", laps=1,
    qualify=False, output="replay.json", no_browser=True,
):
    """Build a namespace mimicking argparse for cmd_race."""

    class Args:
        pass

    a = Args()
    a.car_dir = car_dir
    a.track = track
    a.laps = laps
    a.qualify = qualify
    a.output = output
    a.no_browser = no_browser
    a.seed = 42
    a.league = None
    a.live = False
    return a
