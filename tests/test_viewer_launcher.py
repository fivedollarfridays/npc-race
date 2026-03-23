"""Tests for viewer.launcher -- browser launch for race replays.

T34.0a: Wire webbrowser.open into cmd_run.
"""

import json
import os
from unittest.mock import patch



# -- Cycle 1: _prepare_viewer and launch_viewer core behavior --


class TestPrepareViewer:
    """_prepare_viewer copies replay and returns a URL."""

    def test_copies_replay_to_viewer_dir(self, tmp_path):
        """_prepare_viewer copies the replay file into the viewer directory."""
        from viewer.launcher import _prepare_viewer

        replay = tmp_path / "replay.json"
        replay.write_text(json.dumps({"laps": 1}))

        viewer_dir = tmp_path / "viewer"
        viewer_dir.mkdir()

        url = _prepare_viewer(str(replay), str(viewer_dir))

        copied = viewer_dir / "replay.json"
        assert copied.is_file()
        assert json.loads(copied.read_text()) == {"laps": 1}
        assert url is not None

    def test_returns_url_with_dashboard(self, tmp_path):
        """_prepare_viewer returns a localhost URL pointing to dashboard.html."""
        from viewer.launcher import _prepare_viewer

        replay = tmp_path / "replay.json"
        replay.write_text("{}")

        viewer_dir = tmp_path / "viewer"
        viewer_dir.mkdir()

        url = _prepare_viewer(str(replay), str(viewer_dir))

        assert "localhost" in url
        assert "dashboard.html" in url

    def test_returns_none_when_viewer_dir_missing(self, tmp_path, capsys):
        """_prepare_viewer returns None and prints message if viewer/ missing."""
        from viewer.launcher import _prepare_viewer

        replay = tmp_path / "replay.json"
        replay.write_text("{}")

        url = _prepare_viewer(str(replay), str(tmp_path / "nope"))

        assert url is None
        out = capsys.readouterr().out
        assert "not found" in out.lower()


class TestLaunchViewerGuards:
    """launch_viewer guards: skips under pytest, uses _find_viewer_dir."""

    def test_skips_under_pytest(self, tmp_path):
        """launch_viewer is a no-op when PYTEST_CURRENT_TEST is set."""
        from viewer.launcher import launch_viewer

        # PYTEST_CURRENT_TEST is set by pytest automatically
        assert "PYTEST_CURRENT_TEST" in os.environ

        with patch("viewer.launcher.webbrowser") as mock_wb:
            launch_viewer(str(tmp_path / "replay.json"))

        mock_wb.open.assert_not_called()

    def test_calls_prepare_and_open(self, tmp_path, monkeypatch):
        """launch_viewer calls _prepare_viewer and webbrowser.open."""
        from viewer.launcher import launch_viewer

        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

        replay = tmp_path / "replay.json"
        replay.write_text("{}")

        viewer_dir = tmp_path / "viewer"
        viewer_dir.mkdir()

        with patch("viewer.launcher._find_viewer_dir", return_value=str(viewer_dir)), \
             patch("viewer.launcher.webbrowser") as mock_wb, \
             patch("viewer.launcher.socketserver.TCPServer") as mock_tcp:
            # Make the context manager work
            mock_tcp.return_value.__enter__ = lambda s: s
            mock_tcp.return_value.__exit__ = lambda s, *a: None
            mock_tcp.return_value.serve_forever.side_effect = KeyboardInterrupt
            launch_viewer(str(replay))

        mock_wb.open.assert_called_once()
        url = mock_wb.open.call_args[0][0]
        assert "localhost" in url
        assert "dashboard.html" in url

        # Replay should have been copied
        assert (viewer_dir / "replay.json").is_file()


# -- Cycle 2: --no-browser flag and cmd_run wiring --


class TestCmdRunBrowserFlag:
    """cmd_run should call launch_viewer unless --no-browser is passed."""

    def test_no_browser_flag_accepted(self):
        """The run subparser should accept --no-browser."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["run", "--car-dir", "cars", "--no-browser"])
        assert args.no_browser is True

    def test_no_browser_default_false(self):
        """--no-browser should default to False (browser opens by default)."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["run", "--car-dir", "cars"])
        assert args.no_browser is False

    def test_cmd_run_calls_launch_viewer(self, monkeypatch, tmp_path):
        """cmd_run should call launch_viewer after run_race."""
        import types

        from cli import commands

        called = {}

        def fake_run_race(**kwargs):
            called["run_race"] = kwargs

        def fake_launch(path):
            called["launch_viewer"] = path

        monkeypatch.setattr(commands, "run_race", fake_run_race)
        monkeypatch.setattr(commands, "launch_viewer", fake_launch)

        car_dir = tmp_path / "cars"
        car_dir.mkdir()

        args = types.SimpleNamespace(
            car_dir=str(car_dir), laps=1, seed=42,
            output="replay.json", track=None, league=None,
            no_browser=False, live=True,
        )
        commands.cmd_run(args)

        assert "launch_viewer" in called
        assert called["launch_viewer"] == "replay.json"

    def test_cmd_run_skips_viewer_with_no_browser(self, monkeypatch, tmp_path):
        """cmd_run should NOT call launch_viewer when --no-browser is set."""
        import types

        from cli import commands

        called = {}

        def fake_run_race(**kwargs):
            called["run_race"] = kwargs

        def fake_launch(path):
            called["launch_viewer"] = path

        monkeypatch.setattr(commands, "run_race", fake_run_race)
        monkeypatch.setattr(commands, "launch_viewer", fake_launch)

        car_dir = tmp_path / "cars"
        car_dir.mkdir()

        args = types.SimpleNamespace(
            car_dir=str(car_dir), laps=1, seed=42,
            output="replay.json", track=None, league=None,
            no_browser=True, live=True,
        )
        commands.cmd_run(args)

        assert "launch_viewer" not in called
