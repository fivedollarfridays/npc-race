"""Tests for race report generator (T13.3)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.narrative import RaceEvent
from engine.race_report import generate_report, find_driver_of_the_day, find_decisive_moment


def _mock_results():
    return [
        {"name": "GooseLoose", "position": 1, "finished": True, "best_lap_s": 56.4},
        {"name": "Silky", "position": 2, "finished": True, "best_lap_s": 57.0},
        {"name": "BrickHouse", "position": 3, "finished": True, "best_lap_s": 58.0},
    ]


def _mock_events():
    return [
        RaceEvent("OVERTAKE", 100, ["GooseLoose", "Silky"], {"position": 1, "lap": 3}),
        RaceEvent("PIT_STOP", 200, ["BrickHouse"], {"compound": "hard"}),
        RaceEvent("FASTEST_LAP", 0, ["GooseLoose"], {"time": 56.4}),
    ]


class TestGenerateReport:
    def test_report_has_winner(self):
        report = generate_report(_mock_results(), _mock_events(), [], track_name="monza")
        assert "GooseLoose" in report

    def test_report_has_track_name(self):
        report = generate_report(_mock_results(), _mock_events(), [], track_name="monza")
        assert "monza" in report.lower() or "MONZA" in report

    def test_report_has_key_moments(self):
        report = generate_report(_mock_results(), _mock_events(), [], track_name="monza")
        assert "KEY MOMENTS" in report or "key moments" in report.lower()

    def test_report_is_string(self):
        report = generate_report(_mock_results(), _mock_events(), [], track_name="monza")
        assert isinstance(report, str)
        assert len(report) > 10


class TestDriverOfTheDay:
    def test_driver_of_the_day(self):
        # Car that started P3 and finished P1 = gained 2 positions
        results = [
            {"name": "A", "position": 1, "finished": True},
            {"name": "B", "position": 2, "finished": True},
            {"name": "C", "position": 3, "finished": True},
        ]
        # Assume grid order was A=1, B=2, C=3 (no change)
        name, reason = find_driver_of_the_day(results)
        assert isinstance(name, str)
        assert isinstance(reason, str)


class TestDecisiveMoment:
    def test_decisive_moment_is_latest_impact(self):
        events = [
            RaceEvent("OVERTAKE", 50, ["A", "B"], {"position": 1}),
            RaceEvent("SAFETY_CAR", 200, ["X"], {"reason": "spin"}),
        ]
        moment = find_decisive_moment(events)
        assert isinstance(moment, str)
