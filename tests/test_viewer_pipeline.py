"""T31.5 — Integration tests for the call log -> viewer pipeline."""

import json
import pathlib

import pytest

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from engine import safe_call
from tracks import get_track
from engine.track_gen import interpolate_track

pytestmark = pytest.mark.slow

CARS_DIR = "cars"


@pytest.fixture(scope="module")
def race_replay():
    """Run a 1-lap race once, return replay for all tests."""
    safe_call.TIMEOUT_ENABLED = False
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)
    sim = PartsRaceSim(cars, pts, laps=1, seed=42, track_name="monza",
                       real_length_m=td.get("real_length_m"))
    sim.run(max_ticks=4000)
    replay = sim.export_replay()
    return sim, replay


class TestRaceProducesCallLogs:
    """Cycle 1: race produces call_logs in replay."""

    def test_call_logs_key_exists(self, race_replay):
        _, replay = race_replay
        assert "call_logs" in replay

    def test_call_logs_is_dict(self, race_replay):
        _, replay = race_replay
        assert isinstance(replay["call_logs"], dict)

    def test_call_logs_has_cars(self, race_replay):
        _, replay = race_replay
        assert len(replay["call_logs"]) > 0, "At least one car should have logs"


class TestCallLogsSampledAt1Hz:
    """Cycle 2: call logs sampled at ~1Hz, not every tick."""

    def test_tick_spacing_is_30(self, race_replay):
        _, replay = race_replay
        car_logs = list(replay["call_logs"].values())[0]
        if len(car_logs) >= 2:
            spacing = car_logs[1]["tick"] - car_logs[0]["tick"]
            assert spacing == 30, f"Expected 30 tick spacing, got {spacing}"

    def test_far_fewer_entries_than_ticks(self, race_replay):
        sim, replay = race_replay
        car_logs = list(replay["call_logs"].values())[0]
        total_ticks = sim.tick
        assert len(car_logs) < total_ticks / 10, (
            "Sampled logs should be much fewer than raw ticks"
        )


class TestCallLogEntryStructure:
    """Cycle 3: each call log entry has tick and parts list."""

    def test_entry_has_tick_and_parts(self, race_replay):
        _, replay = race_replay
        car_logs = list(replay["call_logs"].values())[0]
        entry = car_logs[0]
        assert "tick" in entry
        assert "parts" in entry
        assert isinstance(entry["parts"], list)
        assert len(entry["parts"]) > 0

    def test_part_has_name_output_status(self, race_replay):
        _, replay = race_replay
        car_logs = list(replay["call_logs"].values())[0]
        part = car_logs[0]["parts"][0]
        assert "name" in part
        assert "output" in part
        assert "status" in part

    def test_status_values_are_valid(self, race_replay):
        _, replay = race_replay
        valid_statuses = {"ok", "clamped", "glitch", "error"}
        for car_entries in replay["call_logs"].values():
            for entry in car_entries:
                for part in entry["parts"]:
                    assert part["status"] in valid_statuses, (
                        f"Invalid status: {part['status']}"
                    )


class TestReplayReliabilityScores:
    """Cycle 4: replay includes per-car reliability scores."""

    def test_reliability_key_exists(self, race_replay):
        _, replay = race_replay
        assert "reliability" in replay

    def test_reliability_is_dict_with_cars(self, race_replay):
        _, replay = race_replay
        rel = replay["reliability"]
        assert isinstance(rel, dict)
        assert len(rel) > 0

    def test_reliability_values_in_range(self, race_replay):
        _, replay = race_replay
        for car_name, score in replay["reliability"].items():
            assert 0.0 <= score <= 1.0, (
                f"{car_name} reliability {score} out of [0, 1]"
            )


class TestReplayFileSize:
    """Cycle 5: replay file size is reasonable."""

    def test_1lap_replay_under_15mb(self, race_replay):
        """1-lap replay with call logs should stay under 15MB."""
        _, replay = race_replay
        data = json.dumps(replay)
        size_mb = len(data) / (1024 * 1024)
        assert size_mb < 15.0, f"1-lap replay is {size_mb:.1f}MB, expected <15MB"

    def test_call_logs_not_dominant(self, race_replay):
        """Call logs should not be more than 30% of total replay size."""
        _, replay = race_replay
        full_size = len(json.dumps(replay))
        logs_size = len(json.dumps(replay.get("call_logs", {})))
        ratio = logs_size / full_size
        assert ratio < 0.30, (
            f"Call logs are {ratio:.0%} of replay, expected <30%"
        )


class TestViewerFilesExist:
    """Cycle 6: viewer JS and HTML files exist with expected content."""

    def test_code_terminal_js_exists(self):
        p = pathlib.Path("viewer/js/code-terminal.js")
        assert p.is_file(), "viewer/js/code-terminal.js not found"

    def test_code_terminal_has_init(self):
        content = pathlib.Path("viewer/js/code-terminal.js").read_text()
        assert "initCodeTerminal" in content

    def test_code_terminal_has_update(self):
        content = pathlib.Path("viewer/js/code-terminal.js").read_text()
        assert "updateCodeTerminal" in content

    def test_code_terminal_has_grade(self):
        content = pathlib.Path("viewer/js/code-terminal.js").read_text()
        assert "renderCodeGrade" in content

    def test_dashboard_has_terminal_div(self):
        content = pathlib.Path("viewer/dashboard.html").read_text()
        assert "codeTerminal" in content

    def test_main_js_calls_init(self):
        content = pathlib.Path("viewer/js/main.js").read_text()
        assert "initCodeTerminal" in content

    def test_main_js_calls_update(self):
        content = pathlib.Path("viewer/js/main.js").read_text()
        assert "updateCodeTerminal" in content


class TestBackwardCompat:
    """Cycle 7: old replays without call_logs don't crash consumers."""

    def test_replay_without_call_logs(self):
        replay = {"frames": [], "results": [], "ticks_per_sec": 30}
        assert replay.get("call_logs") is None

    def test_replay_without_reliability(self):
        replay = {"frames": [], "results": [], "ticks_per_sec": 30}
        assert replay.get("reliability") is None
