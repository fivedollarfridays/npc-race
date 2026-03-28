"""Tests for engine.tiers — tiered car loading for progressive difficulty."""

from unittest.mock import patch

import pytest

from engine.tiers import TIERS, load_tier_cars, get_tier_for_car


ALL_19_NAMES = [
    "Berserker", "BrickHouse", "Chameleon", "CrossWind", "DriftKing",
    "FoxFire", "Gambler", "GlassCanon", "GooseLoose", "IronSide",
    "NightFury", "PaperWeight", "Phantom", "RustBucket", "Silky",
    "SlipStream", "SteamRoller", "Tortoise", "Vortex",
]


def _fake_all_cars(directory="cars"):
    """Return minimal car dicts with just CAR_NAME for all 19 rivals."""
    return [{"CAR_NAME": n} for n in ALL_19_NAMES]


# --- test_load_rookie_returns_4 ---
@patch("engine.tiers.load_all_cars", side_effect=_fake_all_cars)
def test_load_rookie_returns_4(mock_load):
    cars = load_tier_cars("rookie")
    assert len(cars) == 4


# --- test_load_midfield_returns_10 ---
@patch("engine.tiers.load_all_cars", side_effect=_fake_all_cars)
def test_load_midfield_returns_10(mock_load):
    cars = load_tier_cars("midfield")
    assert len(cars) == 10


# --- test_load_front_returns_15 ---
@patch("engine.tiers.load_all_cars", side_effect=_fake_all_cars)
def test_load_front_returns_15(mock_load):
    cars = load_tier_cars("front")
    assert len(cars) == 15


# --- test_load_full_returns_19 ---
@patch("engine.tiers.load_all_cars", side_effect=_fake_all_cars)
def test_load_full_returns_19(mock_load):
    cars = load_tier_cars("full")
    assert len(cars) == 19


# --- test_invalid_tier_raises ---
def test_invalid_tier_raises():
    with pytest.raises(ValueError, match="Invalid tier"):
        load_tier_cars("legendary")


# --- test_rookie_names_correct ---
@patch("engine.tiers.load_all_cars", side_effect=_fake_all_cars)
def test_rookie_names_correct(mock_load):
    cars = load_tier_cars("rookie")
    names = {c["CAR_NAME"] for c in cars}
    assert names == {"Tortoise", "RustBucket", "PaperWeight", "SteamRoller"}


# --- test_get_tier_for_car ---
def test_get_tier_for_car():
    assert get_tier_for_car("GlassCanon") == "front"
    assert get_tier_for_car("Tortoise") == "rookie"
    assert get_tier_for_car("IronSide") == "midfield"
    assert get_tier_for_car("Silky") == "veterans"
    assert get_tier_for_car("NonExistent") is None


# --- test_all_19_classified ---
def test_all_19_classified():
    """Every rival appears in exactly one tier."""
    all_classified = []
    for names in TIERS.values():
        all_classified.extend(names)
    # All 19 present
    assert sorted(all_classified) == sorted(ALL_19_NAMES)
    # No duplicates
    assert len(all_classified) == len(set(all_classified))
