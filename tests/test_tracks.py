"""Tests for tracks package — data validation and helper functions."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tracks import TRACKS, get_track, list_tracks, random_track


# ─── Track Count ────────────────────────────────────────────────────────────

def test_tracks_count():
    """Exactly 20 named tracks."""
    assert len(TRACKS) == 20


# ─── Required Fields ────────────────────────────────────────────────────────

REQUIRED_FIELDS = {"name", "country", "character", "laps_default", "control_points"}
VALID_CHARACTERS = {"power", "technical", "balanced", "character"}


def test_all_tracks_have_required_fields():
    for key, track in TRACKS.items():
        for field in REQUIRED_FIELDS:
            assert field in track, f"{key} missing field '{field}'"


def test_all_tracks_have_string_name():
    for key, track in TRACKS.items():
        assert isinstance(track["name"], str), f"{key} name not str"
        assert len(track["name"]) > 0, f"{key} name empty"


def test_all_tracks_have_string_country():
    for key, track in TRACKS.items():
        assert isinstance(track["country"], str), f"{key} country not str"
        assert len(track["country"]) > 0, f"{key} country empty"


def test_all_tracks_have_valid_character():
    for key, track in TRACKS.items():
        assert track["character"] in VALID_CHARACTERS, (
            f"{key} character '{track['character']}' not in {VALID_CHARACTERS}"
        )


def test_all_tracks_have_positive_laps_default():
    for key, track in TRACKS.items():
        assert isinstance(track["laps_default"], int), f"{key} laps_default not int"
        assert track["laps_default"] > 0, f"{key} laps_default <= 0"


# ─── Control Points Validation ──────────────────────────────────────────────

def test_control_points_are_lists_of_tuples():
    for key, track in TRACKS.items():
        pts = track["control_points"]
        assert isinstance(pts, list), f"{key} control_points not list"
        for i, pt in enumerate(pts):
            assert isinstance(pt, tuple), f"{key} point {i} not tuple"
            assert len(pt) == 2, f"{key} point {i} not length 2"


def test_control_points_count_in_range():
    """Each track has 10-20 control points."""
    for key, track in TRACKS.items():
        n = len(track["control_points"])
        assert 10 <= n <= 20, f"{key} has {n} points, expected 10-20"


def test_control_points_within_canvas():
    """All x in 50-1100, y in 50-850 (wider canvas for redesigned tracks)."""
    for key, track in TRACKS.items():
        for i, (x, y) in enumerate(track["control_points"]):
            assert 50 <= x <= 1100, f"{key} point {i} x={x} out of [50,1100]"
            assert 50 <= y <= 850, f"{key} point {i} y={y} out of [50,850]"


def test_control_points_are_numeric():
    for key, track in TRACKS.items():
        for i, (x, y) in enumerate(track["control_points"]):
            assert isinstance(x, (int, float)), f"{key} point {i} x not numeric"
            assert isinstance(y, (int, float)), f"{key} point {i} y not numeric"


# ─── Character Distribution ─────────────────────────────────────────────────

def test_power_tracks_count():
    power = [k for k, v in TRACKS.items() if v["character"] == "power"]
    assert len(power) == 4


def test_technical_tracks_count():
    technical = [k for k, v in TRACKS.items() if v["character"] == "technical"]
    assert len(technical) == 3


def test_balanced_tracks_count():
    balanced = [k for k, v in TRACKS.items() if v["character"] == "balanced"]
    assert len(balanced) == 5


def test_character_tracks_count():
    character = [k for k, v in TRACKS.items() if v["character"] == "character"]
    assert len(character) == 8


# ─── Specific Track Names ───────────────────────────────────────────────────

EXPECTED_NAMES = [
    "monza", "baku", "jeddah", "spa",
    "monaco", "singapore", "zandvoort",
    "silverstone", "suzuka", "austin", "barcelona", "bahrain",
    "interlagos", "imola", "melbourne", "montreal",
    "mugello", "lusail", "hungaroring", "shanghai",
]


def test_all_expected_tracks_present():
    for name in EXPECTED_NAMES:
        assert name in TRACKS, f"Track '{name}' missing from TRACKS"


# ─── Helper Functions ────────────────────────────────────────────────────────

def test_get_track_returns_dict():
    track = get_track("monza")
    assert isinstance(track, dict)
    assert track["name"] == "Monza"


def test_get_track_raises_key_error():
    try:
        get_track("nonexistent")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass


def test_list_tracks_returns_sorted():
    names = list_tracks()
    assert isinstance(names, list)
    assert names == sorted(names)
    assert len(names) == 20


def test_random_track_returns_valid_key():
    key = random_track()
    assert key in TRACKS


def test_random_track_returns_string():
    key = random_track()
    assert isinstance(key, str)


# ─── Key Matches Name ────────────────────────────────────────────────────────

def test_dict_keys_are_lowercase_names():
    for key, track in TRACKS.items():
        assert key == track["name"].lower(), (
            f"Key '{key}' doesn't match lowercase name '{track['name'].lower()}'"
        )
