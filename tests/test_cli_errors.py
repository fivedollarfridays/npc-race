"""Tests for CLI error handling — bugs #4, #5, #6 from T38.2.

Bug 4: Invalid track name should abort, not proceed on random track.
Bug 5: main() should propagate non-zero return codes via sys.exit.
Bug 6: Bad car-dir should show friendly error, not traceback.
"""

import types

import pytest


# ── Cycle 1: Bug 4 — invalid track aborts with return code 1 ──


class TestInvalidTrackAborts:
    """cmd_run must return 1 when --track is set but resolves to None."""

    def test_invalid_track_exits_nonzero(self, monkeypatch, capsys):
        """Run with an invalid track name should return 1, not proceed."""
        from cli import commands

        called = False

        def fake_run_race(**kwargs):
            nonlocal called
            called = True
            return []

        monkeypatch.setattr(commands, "run_race", fake_run_race)

        import tempfile

        with tempfile.TemporaryDirectory() as td:
            args = types.SimpleNamespace(
                car_dir=td, laps=1, seed=42, output="out.json",
                track="bogus_nonexistent_track", league=None,
                live=False, no_browser=True, verbose=False,
            )
            result = commands.cmd_run(args)

        assert result == 1, "cmd_run should return 1 for invalid track"
        assert not called, "run_race should NOT be called with invalid track"
        captured = capsys.readouterr()
        assert "unknown track" in captured.out.lower()


# ── Cycle 2: Bug 5 — main() propagates return codes via sys.exit ──


class TestMainPropagatesReturnCodes:
    """main() must call sys.exit when handler returns non-zero."""

    def test_init_existing_dir_exits_nonzero_via_main(self, capsys):
        """init on existing dir should exit 1 through main()."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main(["init", "default_project"])
        assert exc_info.value.code == 1

    def test_run_missing_cardir_exits_nonzero_via_main(self, capsys):
        """run with bad car dir should exit 1 through main()."""
        from cli.main import main

        with pytest.raises(SystemExit) as exc_info:
            main(["run", "--car-dir", "/nonexistent/path"])
        assert exc_info.value.code == 1


# ── Cycle 3: Bug 6 — bad car-dir shows friendly error, no traceback ──


class TestBadCarDirNoTraceback:
    """Loading a car project dir with bad files should not traceback."""

    def test_bad_cardir_no_traceback(self, monkeypatch, capsys, tmp_path):
        """run_race raising ValueError should be caught and return 1."""
        from cli import commands

        def fake_run_race(**kwargs):
            raise ValueError("No valid car files found in directory")

        monkeypatch.setattr(commands, "run_race", fake_run_race)

        args = types.SimpleNamespace(
            car_dir=str(tmp_path), laps=1, seed=42, output="out.json",
            track=None, league=None,
            live=False, no_browser=True, verbose=False,
        )
        result = commands.cmd_run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()

    def test_bad_cardir_filenotfound(self, monkeypatch, capsys, tmp_path):
        """run_race raising FileNotFoundError should be caught."""
        from cli import commands

        def fake_run_race(**kwargs):
            raise FileNotFoundError("car.py not found")

        monkeypatch.setattr(commands, "run_race", fake_run_race)

        args = types.SimpleNamespace(
            car_dir=str(tmp_path), laps=1, seed=42, output="out.json",
            track=None, league=None,
            live=False, no_browser=True, verbose=False,
        )
        result = commands.cmd_run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()


# ── Cycle 4: T43.4 — CLI exit codes: all commands return int ──


class TestValidateExitCodes:
    """cmd_validate must return 0 on all-pass, 1 on any failure."""

    def test_validate_fail_exits_nonzero(self, monkeypatch, capsys):
        """Validating a non-existent file should return 1."""
        from cli import commands

        fail_result = types.SimpleNamespace(passed=False, violations=["bad"])
        monkeypatch.setattr(
            commands, "scan_car_file", lambda path: fail_result,
        )

        args = types.SimpleNamespace(car_files=["nonexistent.py"])
        result = commands.cmd_validate(args)
        assert result == 1, "cmd_validate should return 1 when a file fails"

    def test_validate_pass_exits_zero(self, monkeypatch, capsys):
        """Validating a passing file should return 0."""
        from cli import commands

        pass_result = types.SimpleNamespace(passed=True, violations=[])
        monkeypatch.setattr(
            commands, "scan_car_file", lambda path: pass_result,
        )

        args = types.SimpleNamespace(car_files=["good.py"])
        result = commands.cmd_validate(args)
        assert result == 0, "cmd_validate should return 0 on all-pass"


class TestListTracksExitCode:
    """cmd_list_tracks must return 0."""

    def test_list_tracks_exits_zero(self, capsys):
        from cli.commands import cmd_list_tracks

        result = cmd_list_tracks(types.SimpleNamespace())
        assert result == 0, "cmd_list_tracks should return 0"


class TestQualifyExitCodes:
    """cmd_qualify must return 1 on errors, 0 on success."""

    def test_qualify_bad_track_exits_nonzero(self, capsys):
        from cli.race_commands import cmd_qualify

        args = types.SimpleNamespace(
            car_dir="cars", track="bogus_nonexistent_track",
            output="grid.json",
        )
        result = cmd_qualify(args)
        assert result == 1, "cmd_qualify should return 1 for invalid track"

    def test_qualify_bad_cardir_exits_nonzero(self, capsys):
        from cli.race_commands import cmd_qualify

        args = types.SimpleNamespace(
            car_dir="/nonexistent/path", track="monza",
            output="grid.json",
        )
        result = cmd_qualify(args)
        assert result == 1, "cmd_qualify should return 1 for bad car dir"


class TestRaceExitCodes:
    """cmd_race must return 1 on errors, 0 on success."""

    def test_race_bad_cardir_exits_nonzero(self, capsys):
        from cli.race_commands import cmd_race

        args = types.SimpleNamespace(
            car_dir="/nonexistent/path", track="monza", laps=1,
            qualify=False, output="replay.json", seed=42,
            league=None, live=False, verbose=False,
        )
        result = cmd_race(args)
        assert result == 1, "cmd_race should return 1 for bad car dir"

    def test_race_bad_track_via_qualify_exits_nonzero(self, capsys):
        from cli.race_commands import cmd_race

        args = types.SimpleNamespace(
            car_dir="cars", track="bogus_nonexistent_track", laps=1,
            qualify=True, output="replay.json", seed=42,
            league=None, live=False, verbose=False,
        )
        result = cmd_race(args)
        assert result == 1, "cmd_race should return 1 for bad track"


class TestTournamentExitCodes:
    """cmd_tournament must return 1 on invalid tracks."""

    def test_tournament_invalid_tracks_exits_nonzero(self, capsys):
        from cli.commands import cmd_tournament

        args = types.SimpleNamespace(
            tracks="bogus_nonexistent", races=1, laps=1,
            car_dir="cars", data_dir=None, output_dir="/tmp/tourn_test",
        )
        result = cmd_tournament(args)
        assert result == 1, "cmd_tournament should return 1 for invalid tracks"


class TestSeasonExitCode:
    """cmd_season must return int."""

    def test_season_returns_int(self, monkeypatch, capsys):
        from cli import commands

        def fake_run_season(**kwargs):
            pass

        monkeypatch.setattr(
            "engine.season_runner.run_season", fake_run_season,
        )
        args = types.SimpleNamespace(
            car_dir="cars", calendar="short", tracks=None,
            laps=1, output_dir="/tmp/season_test",
        )
        result = commands.cmd_season(args)
        assert result == 0, "cmd_season should return 0 on success"
