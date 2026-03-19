"""Tests for season calendar (T16.1)."""
from engine.season import get_season, create_custom_season, list_seasons
from tracks import list_tracks


class TestGetSeason:
    def test_get_short_season(self):
        s = get_season("short")
        assert len(s["races"]) == 5

    def test_get_full_season(self):
        s = get_season("full")
        assert len(s["races"]) == 10

    def test_season_has_valid_tracks(self):
        available = set(list_tracks())
        for name in list_seasons():
            s = get_season(name)
            for race in s["races"]:
                assert race["track"] in available, f"{race['track']} not in tracks"

    def test_custom_season(self):
        s = create_custom_season(["monza", "monaco"], laps=3)
        assert len(s["races"]) == 2
        assert s["races"][0]["laps"] == 3

    def test_list_seasons(self):
        names = list_seasons()
        assert "short" in names
        assert "full" in names
        assert "classic" in names
