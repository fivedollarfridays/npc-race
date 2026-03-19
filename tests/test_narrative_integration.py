"""Sprint 13 integration gate — narrative verification (T13.5)."""

import json
import pathlib
import tempfile

import pytest

from engine.race_runner import run_race

pytestmark = pytest.mark.slow

CARS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "cars")


class TestNarrativeOutput:
    def test_events_detected_in_race(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        run_race(car_dir=CARS_DIR, track_name="monza", laps=3, output=out)
        with open(out) as f:
            replay = json.load(f)
        assert "events" in replay
        assert isinstance(replay["events"], list)

    def test_commentary_generated(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        run_race(car_dir=CARS_DIR, track_name="monza", laps=3, output=out)
        with open(out) as f:
            replay = json.load(f)
        assert "commentary" in replay
        assert isinstance(replay["commentary"], list)

    def test_race_report_generated(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        run_race(car_dir=CARS_DIR, track_name="monza", laps=3, output=out)
        with open(out) as f:
            replay = json.load(f)
        assert "race_report" in replay
        assert isinstance(replay["race_report"], str)
        assert len(replay["race_report"]) > 20

    def test_report_contains_winner(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        run_race(car_dir=CARS_DIR, track_name="monza", laps=2, output=out)
        with open(out) as f:
            replay = json.load(f)
        results = replay["results"]
        winner = results[0]["name"]
        assert winner in replay["race_report"]


class TestArchCompliance:
    def test_narrative_under_limits(self):
        lines = len(pathlib.Path("engine/narrative.py").read_text().splitlines())
        assert lines <= 140, f"narrative.py has {lines} lines"

    def test_commentary_under_limits(self):
        lines = len(pathlib.Path("engine/commentary.py").read_text().splitlines())
        assert lines <= 80, f"commentary.py has {lines} lines"

    def test_race_report_under_limits(self):
        lines = len(pathlib.Path("engine/race_report.py").read_text().splitlines())
        assert lines <= 100, f"race_report.py has {lines} lines"

    def test_simulation_unchanged(self):
        lines = len(pathlib.Path("engine/simulation.py").read_text().splitlines())
        assert lines <= 400, f"simulation.py has {lines} lines"
        text = pathlib.Path("engine/simulation.py").read_text()
        count = text.count("\n    def ") + text.count("\ndef ")
        assert count <= 15, f"simulation.py has {count} functions"
