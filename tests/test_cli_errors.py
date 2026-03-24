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
