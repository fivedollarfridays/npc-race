"""Tests for real-world track data (real_length_m, real_laps) on all 20 tracks."""

from tracks import TRACKS, get_track


class TestAllTracksHaveRealData:
    """Every track must have real_length_m and real_laps fields."""

    def test_every_track_has_real_length_m(self):
        for key, track in TRACKS.items():
            assert "real_length_m" in track, f"{key} missing real_length_m"

    def test_every_track_has_real_laps(self):
        for key, track in TRACKS.items():
            assert "real_laps" in track, f"{key} missing real_laps"

    def test_real_length_m_is_positive_int(self):
        for key, track in TRACKS.items():
            val = track["real_length_m"]
            assert isinstance(val, int), f"{key} real_length_m not int: {type(val)}"
            assert val > 0, f"{key} real_length_m not positive: {val}"

    def test_real_laps_is_positive_int(self):
        for key, track in TRACKS.items():
            val = track["real_laps"]
            assert isinstance(val, int), f"{key} real_laps not int: {type(val)}"
            assert val > 0, f"{key} real_laps not positive: {val}"


class TestSpotCheckValues:
    """Verify known real-world values for specific tracks."""

    def test_monaco_length(self):
        assert get_track("monaco")["real_length_m"] == 3337

    def test_monaco_laps(self):
        assert get_track("monaco")["real_laps"] == 78

    def test_monza_length(self):
        assert get_track("monza")["real_length_m"] == 5793

    def test_monza_laps(self):
        assert get_track("monza")["real_laps"] == 53

    def test_spa_length(self):
        assert get_track("spa")["real_length_m"] == 7004

    def test_spa_laps(self):
        assert get_track("spa")["real_laps"] == 44

    def test_interlagos_length(self):
        assert get_track("interlagos")["real_length_m"] == 4309

    def test_interlagos_laps(self):
        assert get_track("interlagos")["real_laps"] == 71
