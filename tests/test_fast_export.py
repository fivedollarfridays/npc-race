"""Tests for fast mode export: lap_summary.json and fast-mode run_race."""

import json
import os

from engine.fast_export import export_lap_summary
from engine.race_runner import run_race
from cli.main import _build_parser


# --- Helpers ---

def _run_fast(tmp_path, fast_mode=True):
    """Run a minimal 1-lap race into tmp_path, return output dir."""
    output = str(tmp_path / "replay.json")
    run_race(
        car_dir="cars",
        laps=1,
        track_name="monza",
        output=output,
        fast_mode=fast_mode,
    )
    return tmp_path


# --- Cycle 1: export_lap_summary unit tests ---


class TestExportLapSummary:
    """export_lap_summary writes lap_summary.json from sim data."""

    def test_writes_valid_json(self, tmp_path):
        """export_lap_summary writes a JSON file that can be loaded."""

        class FakeSim:
            def get_lap_summaries(self):
                return {
                    "CarA": [{"lap": 1, "time_s": 80.5}],
                    "CarB": [{"lap": 1, "time_s": 81.2}],
                }

        path = str(tmp_path / "lap_summary.json")
        export_lap_summary(FakeSim(), path)

        assert os.path.isfile(path)
        with open(path) as f:
            data = json.load(f)

        assert "CarA" in data
        assert "CarB" in data
        assert data["CarA"][0]["lap"] == 1
        assert data["CarA"][0]["time_s"] == 80.5

    def test_empty_summaries(self, tmp_path):
        """export_lap_summary handles empty summaries gracefully."""

        class FakeSim:
            def get_lap_summaries(self):
                return {}

        path = str(tmp_path / "lap_summary.json")
        export_lap_summary(FakeSim(), path)

        with open(path) as f:
            data = json.load(f)
        assert data == {}


# --- Cycle 2: fast mode integration ---


class TestFastModeRunRace:
    """run_race(fast_mode=True) writes results + lap_summary, skips replay."""

    def test_fast_mode_writes_results_json(self, tmp_path):
        d = _run_fast(tmp_path, fast_mode=True)
        assert os.path.isfile(str(d / "results.json"))

    def test_fast_mode_writes_lap_summary_json(self, tmp_path):
        d = _run_fast(tmp_path, fast_mode=True)
        assert os.path.isfile(str(d / "lap_summary.json"))

    def test_fast_mode_skips_replay_json(self, tmp_path):
        d = _run_fast(tmp_path, fast_mode=True)
        assert not os.path.isfile(str(d / "replay.json"))

    def test_lap_summary_has_per_car_data(self, tmp_path):
        d = _run_fast(tmp_path, fast_mode=True)
        with open(str(d / "lap_summary.json")) as f:
            data = json.load(f)
        # Should have at least 2 cars (from cars/ directory)
        assert len(data) >= 2
        # Each car should have at least 1 lap entry
        for car_name, laps in data.items():
            assert len(laps) >= 1
            assert "lap" in laps[0]
            assert "time_s" in laps[0]


# --- Cycle 3: normal mode unchanged ---


class TestNormalModeUnchanged:
    """run_race(fast_mode=False) still writes replay.json as before."""

    def test_normal_mode_writes_replay_json(self, tmp_path):
        d = _run_fast(tmp_path, fast_mode=False)
        assert os.path.isfile(str(d / "replay.json"))


# --- Cycle 4: CLI --live flag ---


class TestCLILiveFlag:
    """CLI --live flag controls fast_mode."""

    def test_default_no_live_flag(self):
        """Without --live, args.live is False (fast mode is default)."""
        parser = _build_parser()
        args = parser.parse_args(["run"])
        assert args.live is False

    def test_live_flag_present(self):
        """With --live, args.live is True."""
        parser = _build_parser()
        args = parser.parse_args(["run", "--live"])
        assert args.live is True


# --- Cycle 5: cmd_run wiring ---


class TestCmdRunWiring:
    """cmd_run passes fast_mode and controls viewer launch."""

    def test_default_run_passes_fast_mode_true(self, monkeypatch):
        """Without --live, run_race is called with fast_mode=True."""
        captured = {}

        def fake_run_race(**kwargs):
            captured.update(kwargs)
            return []

        monkeypatch.setattr("cli.commands.run_race", fake_run_race)
        monkeypatch.setattr("os.path.isdir", lambda _: True)

        from cli.commands import cmd_run

        class Args:
            car_dir = "cars"
            laps = 1
            seed = 42
            output = "replay.json"
            track = None
            league = None
            live = False
            no_browser = False

        cmd_run(Args())
        assert captured["fast_mode"] is True

    def test_live_run_passes_fast_mode_false(self, monkeypatch):
        """With --live, run_race is called with fast_mode=False."""
        captured = {}

        def fake_run_race(**kwargs):
            captured.update(kwargs)
            return []

        monkeypatch.setattr("cli.commands.run_race", fake_run_race)
        monkeypatch.setattr("os.path.isdir", lambda _: True)

        launched = []
        monkeypatch.setattr(
            "cli.commands.launch_viewer", lambda p: launched.append(p)
        )

        from cli.commands import cmd_run

        class Args:
            car_dir = "cars"
            laps = 1
            seed = 42
            output = "replay.json"
            track = None
            league = None
            live = True
            no_browser = False

        cmd_run(Args())
        assert captured["fast_mode"] is False
        assert len(launched) == 1  # viewer launched in live mode

    def test_fast_mode_no_viewer(self, monkeypatch):
        """Without --live (fast mode), viewer is NOT launched."""
        monkeypatch.setattr(
            "cli.commands.run_race", lambda **kw: []
        )
        monkeypatch.setattr("os.path.isdir", lambda _: True)

        launched = []
        monkeypatch.setattr(
            "cli.commands.launch_viewer", lambda p: launched.append(p)
        )

        from cli.commands import cmd_run

        class Args:
            car_dir = "cars"
            laps = 1
            seed = 42
            output = "replay.json"
            track = None
            league = None
            live = False
            no_browser = False

        cmd_run(Args())
        assert len(launched) == 0  # no viewer in fast mode
