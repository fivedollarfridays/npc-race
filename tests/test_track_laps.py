"""Tests for track real lap counts as defaults."""

from tracks import TRACKS


EXPECTED_LAPS = {
    "monza": 53,
    "baku": 51,
    "jeddah": 50,
    "spa": 44,
    "silverstone": 52,
    "suzuka": 53,
    "austin": 56,
    "barcelona": 66,
    "bahrain": 57,
    "monaco": 78,
    "singapore": 62,
    "zandvoort": 72,
    "interlagos": 71,
    "imola": 63,
    "melbourne": 58,
    "montreal": 70,
    "mugello": 59,
    "lusail": 57,
    "hungaroring": 70,
    "shanghai": 56,
}


def test_all_20_tracks_present() -> None:
    """All 20 tracks exist in the registry."""
    assert len(TRACKS) == 20
    for key in EXPECTED_LAPS:
        assert key in TRACKS, f"Missing track: {key}"


def test_all_tracks_have_real_laps_field() -> None:
    """Every track must have a real_laps field."""
    for key, track in TRACKS.items():
        assert "real_laps" in track, f"{key} missing real_laps"


def test_laps_default_equals_real_laps() -> None:
    """laps_default must equal real_laps for every track."""
    for key, track in TRACKS.items():
        assert track["laps_default"] == track["real_laps"], (
            f"{key}: laps_default={track['laps_default']} != real_laps={track['real_laps']}"
        )


def test_laps_default_matches_expected() -> None:
    """laps_default matches the official F1 values."""
    for key, expected in EXPECTED_LAPS.items():
        track = TRACKS[key]
        assert track["laps_default"] == expected, (
            f"{key}: laps_default={track['laps_default']} != expected={expected}"
        )


def test_all_laps_positive_and_reasonable() -> None:
    """All lap counts must be between 30 and 100 (F1 range)."""
    for key, track in TRACKS.items():
        laps = track["laps_default"]
        assert 30 < laps < 100, f"{key}: laps_default={laps} outside 30-100 range"
        real = track["real_laps"]
        assert 30 < real < 100, f"{key}: real_laps={real} outside 30-100 range"
