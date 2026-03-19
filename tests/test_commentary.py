"""Tests for commentary generator (T13.2)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.narrative import RaceEvent
from engine.commentary import format_event, format_events, format_time


class TestFormatEvent:
    def test_format_overtake(self):
        e = RaceEvent("OVERTAKE", 100, ["GooseLoose", "Silky"], {"position": 2, "lap": 5})
        text = format_event(e)
        assert "GooseLoose" in text
        assert "Silky" in text

    def test_format_battle(self):
        e = RaceEvent("BATTLE", 200, ["A", "B"], {"gap": 0.8, "duration_frames": 90})
        text = format_event(e)
        assert "BATTLE" in text
        assert "A" in text and "B" in text

    def test_format_pit_stop(self):
        e = RaceEvent("PIT_STOP", 300, ["BrickHouse"], {"compound": "hard"})
        text = format_event(e)
        assert "PIT" in text
        assert "BrickHouse" in text

    def test_format_safety_car(self):
        e = RaceEvent("SAFETY_CAR", 400, ["X"], {"reason": "collision"})
        text = format_event(e)
        assert "SAFETY CAR" in text

    def test_format_spin(self):
        e = RaceEvent("SPIN", 500, ["SlipStream"])
        text = format_event(e)
        assert "SPIN" in text
        assert "SlipStream" in text

    def test_format_fastest_lap(self):
        e = RaceEvent("FASTEST_LAP", 0, ["GooseLoose"], {"time": 56.4})
        text = format_event(e)
        assert "FASTEST LAP" in text
        assert "GooseLoose" in text


class TestFormatTime:
    def test_format_time(self):
        assert format_time(65.5) == "1:05.500"

    def test_format_time_under_minute(self):
        assert format_time(45.123) == "0:45.123"


class TestFormatEvents:
    def test_format_events_list(self):
        events = [
            RaceEvent("OVERTAKE", 100, ["A", "B"], {"position": 1, "lap": 3}),
            RaceEvent("SPIN", 200, ["C"]),
        ]
        result = format_events(events)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(s, str) for s in result)
