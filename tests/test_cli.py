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
        """validate on an invalid car file should report FAIL."""
        car = tmp_path / "bad_car.py"
        car.write_text("import os\n")
        from cli.main import main

        main(["validate", str(car)])
        captured = capsys.readouterr()
        assert "fail" in captured.out.lower()

    def test_validate_missing_file(self, capsys):
        """validate on a missing file should report error."""
        from cli.main import main

        main(["validate", "/nonexistent/car.py"])
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
    """Test the init subcommand."""

    def test_init_creates_cars_dir(self, tmp_path, capsys):
        """init should create a cars/ directory with a template car."""
        from cli.main import main

        target = tmp_path / "cars"
        main(["init", "--dir", str(target)])
        assert target.is_dir()
        files = list(target.iterdir())
        assert len(files) == 1
        content = files[0].read_text()
        assert "CAR_NAME" in content

    def test_init_default_dir(self, capsys, monkeypatch, tmp_path):
        """init with no --dir should create cars/ in cwd."""
        monkeypatch.chdir(tmp_path)
        from cli.main import main

        main(["init"])
        assert (tmp_path / "cars").is_dir()

    def test_init_existing_dir_no_overwrite(self, tmp_path, capsys):
        """init on existing cars/ dir should not overwrite existing files."""
        target = tmp_path / "cars"
        target.mkdir()
        existing = target / "my_car.py"
        existing.write_text("# my car")
        from cli.main import main

        main(["init", "--dir", str(target)])
        assert existing.read_text() == "# my car"


class TestRunCommand:
    """Test the run subcommand."""

    def test_run_missing_car_dir(self, capsys):
        """run with nonexistent car dir should print error."""
        from cli.main import main

        main(["run", "--car-dir", "/nonexistent/path"])
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


class TestWizardStub:
    """Test that wizard subcommand is registered but stubbed."""

    def test_wizard_prints_stub(self, capsys):
        """wizard should print a 'not yet implemented' message."""
        from cli.main import main

        main(["wizard"])
        captured = capsys.readouterr()
        assert "not yet implemented" in captured.out.lower() or "coming soon" in captured.out.lower()
