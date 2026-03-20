"""Tests for championship points system (T16.2)."""
from engine.championship import (
    create_standings, award_points, get_sorted_standings, format_standings,
)


class TestCreateStandings:
    def test_create_standings_empty(self):
        s = create_standings()
        assert isinstance(s, dict)
        assert len(s) == 0


class TestAwardPoints:
    def test_award_points_p1(self):
        s = create_standings()
        results = [{"name": "A", "position": 1}]
        award_points(s, results)
        assert s["A"]["points"] == 25

    def test_award_points_p10(self):
        s = create_standings()
        award_points(s, [{"name": "A", "position": 10}])
        assert s["A"]["points"] == 1

    def test_award_points_p11(self):
        s = create_standings()
        award_points(s, [{"name": "A", "position": 11}])
        assert s["A"]["points"] == 0

    def test_cumulative_points(self):
        s = create_standings()
        award_points(s, [{"name": "A", "position": 1}])
        award_points(s, [{"name": "A", "position": 2}])
        assert s["A"]["points"] == 25 + 18


class TestSortedStandings:
    def test_sorted_standings(self):
        s = create_standings()
        award_points(s, [{"name": "A", "position": 2}, {"name": "B", "position": 1}])
        sorted_s = get_sorted_standings(s)
        assert sorted_s[0][0] == "B"

    def test_tiebreaker_wins(self):
        s = {"A": {"points": 25, "wins": 1, "podiums": 1},
             "B": {"points": 25, "wins": 0, "podiums": 2}}
        sorted_s = get_sorted_standings(s)
        assert sorted_s[0][0] == "A"


class TestFormatStandings:
    def test_format_standings(self):
        s = create_standings()
        award_points(s, [{"name": "A", "position": 1}])
        text = format_standings(s)
        assert isinstance(text, str)
        assert "A" in text
        assert "25" in text
