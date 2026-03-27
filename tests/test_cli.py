"""Tests for the CLI package — dispatcher, commands, and integration."""

import tempfile

import pytest


# ── Cycle 1: CLI structure and dispatcher ──


class TestCLIDispatcher:
    """Test that the main() dispatcher handles subcommands."""

    def test_no_args_prints_help(self, capsys):
        """Running with no args should print help and exit cleanly."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main([])
        # argparse exits 2 when required subcommand is missing
        assert exc_info.value.code == 2

    def test_help_flag(self, capsys):
        """--help should print help text and exit 0."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "npcrace" in captured.out.lower() or "npc" in captured.out.lower()

    def test_unknown_subcommand(self):
        """Unknown subcommand should exit with error."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main(["bogus"])
        assert exc_info.value.code == 2


class TestListTracksCommand:
    """Test the list-tracks subcommand."""

    def test_list_tracks_prints_tracks(self, capsys):
        """list-tracks should print track names."""
        from cli.main import main

        main(["list-tracks"])
        captured = capsys.readouterr()
        assert "monza" in captured.out.lower()
        assert "monaco" in captured.out.lower()

    def test_list_tracks_shows_count(self, capsys):
        """list-tracks should show the total count."""
        from cli.main import main

        main(["list-tracks"])
        captured = capsys.readouterr()
        assert "20" in captured.out


class TestValidateCommand:
    """Test the validate subcommand."""

    def test_validate_valid_car(self, capsys, tmp_path):
        """validate on a valid car file should report PASS."""
        car = tmp_path / "good_car.py"
        car.write_text(
            'CAR_NAME = "Test"\n'
            'CAR_COLOR = "#ff0000"\n'
            "POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n"
            "def strategy(state):\n"
            '    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}\n'
        )
        from cli.main import main

        main(["validate", str(car)])
        captured = capsys.readouterr()
        assert "pass" in captured.out.lower()

    def test_validate_invalid_car(self, capsys, tmp_path):
        """validate on an invalid car file should report FAIL and exit 1."""
        car = tmp_path / "bad_car.py"
        car.write_text("import os\n")
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main(["validate", str(car)])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "fail" in captured.out.lower()

    def test_validate_missing_file(self, capsys):
        """validate on a missing file should report error and exit 1."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main(["validate", "/nonexistent/car.py"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "fail" in captured.out.lower()

    def test_validate_multiple_files(self, capsys, tmp_path):
        """validate should accept multiple positional args."""
        car1 = tmp_path / "car1.py"
        car2 = tmp_path / "car2.py"
        for car in (car1, car2):
            car.write_text(
                'CAR_NAME = "Test"\nCAR_COLOR = "#ff0000"\n'
                "POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n"
                "def strategy(state):\n"
                '    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}\n'
            )
        from cli.main import main

        main(["validate", str(car1), str(car2)])
        captured = capsys.readouterr()
        assert captured.out.lower().count("pass") >= 2


class TestInitCommand:
    """Test the init subcommand creates inside cars/ with PascalCase name."""

    def test_init_creates_inside_cars(self, capsys):
        """init my_car creates cars/my_car/ with F3 template files."""
        import os
        import shutil

        name = "_test_cli_init"
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target = os.path.join(root, "cars", name)
        try:
            from cli.main import main

            main(["init", name])
            assert os.path.isdir(target)
            assert os.path.isfile(os.path.join(target, "car.py"))
            assert os.path.isfile(os.path.join(target, "gearbox.py"))
            assert os.path.isfile(os.path.join(target, "cooling.py"))
            assert os.path.isfile(os.path.join(target, "strategy.py"))
        finally:
            if os.path.isdir(target):
                shutil.rmtree(target)

    def test_init_rejects_absolute_path(self, capsys):
        """init with absolute path returns error code 1."""
        from cli.commands import cmd_init

        import types
        args = types.SimpleNamespace(dir="/tmp/foo")
        result = cmd_init(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "simple directory name" in captured.out

    def test_init_existing_dir_no_overwrite(self, capsys):
        """init on existing dir should return error code 1."""
        from cli.commands import cmd_init

        import types
        # "default_project" already exists in cars/
        args = types.SimpleNamespace(dir="default_project")
        result = cmd_init(args)
        assert result == 1


class TestRunCommand:
    """Test the run subcommand."""

    def test_run_missing_car_dir(self, capsys):
        """run with nonexistent car dir should print error and exit 1."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main(["run", "--car-dir", "/nonexistent/path"])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_run_passes_args_to_engine(self, monkeypatch):
        """run should call engine.run_race with correct args."""
        from cli import commands

        called_with = {}

        def fake_run_race(**kwargs):
            called_with.update(kwargs)
            return []

        monkeypatch.setattr(commands, "run_race", fake_run_race)
        # Need a real car dir
        from cli.main import main

        with tempfile.TemporaryDirectory() as td:
            main(["run", "--car-dir", td, "--laps", "5", "--seed", "99",
                  "--output", "out.json"])
        assert called_with["car_dir"] == td
        assert called_with["laps"] == 5
        assert called_with["track_seed"] == 99
        assert called_with["output"] == "out.json"

    def test_run_with_track_flag(self, monkeypatch):
        """run --track monza should pass track_name to engine."""
        from cli import commands

        called_with = {}

        def fake_run_race(**kwargs):
            called_with.update(kwargs)
            return []

        monkeypatch.setattr(commands, "run_race", fake_run_race)
        from cli.main import main

        with tempfile.TemporaryDirectory() as td:
            main(["run", "--car-dir", td, "--track", "monza"])
        assert called_with["track_name"] == "monza"


class TestWizardRemoved:
    """Wizard command was removed (stub had no implementation)."""

    def test_wizard_not_in_parser(self):
        """wizard should not be a valid subcommand."""
        from cli.main import _build_parser

        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["wizard"])
