"""Tests for engine/ghost.py — ghost car system."""

from __future__ import annotations


# ---- Cycle 1: basic creation and validation ----

def test_create_ghost_level_1():
    """Level 1 ghost returns valid car dict with CAR_NAME='Ghost'."""
    from engine.ghost import create_ghost

    car = create_ghost(1)
    assert car["CAR_NAME"] == "Ghost"
    assert car["CAR_COLOR"] == "#555555"
    assert isinstance(car["POWER"], (int, float))
    assert "parts" in car
    assert "engine_spec" in car


def test_invalid_level_raises():
    """Level 0 or 6 raises ValueError."""
    import pytest
    from engine.ghost import create_ghost

    with pytest.raises(ValueError, match="Invalid ghost level"):
        create_ghost(0)
    with pytest.raises(ValueError, match="Invalid ghost level"):
        create_ghost(6)


# ---- Cycle 2: part function behavior ----

def test_ghost_gearbox_shifts_at_config_rpm():
    """Level 1 ghost shifts up at 14000 RPM."""
    from engine.ghost import create_ghost

    car = create_ghost(1)
    gearbox = car["parts"]["gearbox"]
    # At 14001 RPM in gear 3, should shift up
    assert gearbox(14001, 200, 3, 1.0) == 4
    # At 13000 RPM in gear 3, should stay
    assert gearbox(13000, 200, 3, 1.0) == 3


def test_ghost_cooling_returns_config_effort():
    """Level 3 ghost returns cooling effort 1.0."""
    from engine.ghost import create_ghost

    car = create_ghost(3)
    cooling = car["parts"]["cooling"]
    assert cooling(90, 400, 45, 200) == 1.0


def test_ghost_strategy_no_pit_level_4():
    """Level 4 ghost never pits (threshold 999)."""
    from engine.ghost import create_ghost

    car = create_ghost(4)
    strategy = car["parts"]["strategy"]
    # Even at 99% tire wear, no pit
    result = strategy({"tire_wear": 0.99})
    assert "pit_request" not in result


# ---- Cycle 3: all levels produce valid dicts, parts completeness ----

def test_all_levels_valid():
    """Levels 1-5 all produce car dicts with required fields."""
    from engine.ghost import create_ghost

    required = {"CAR_NAME", "CAR_COLOR", "POWER", "GRIP", "WEIGHT",
                "AERO", "BRAKES", "parts", "engine_spec"}
    for level in range(1, 6):
        car = create_ghost(level)
        missing = required - set(car.keys())
        assert not missing, f"Level {level} missing: {missing}"


def test_ghost_has_parts_dict():
    """All ghost levels have 'parts' dict with 10 entries."""
    from engine.ghost import create_ghost
    from engine.parts_api import CAR_PARTS

    for level in range(1, 6):
        car = create_ghost(level)
        assert "parts" in car, f"Level {level} missing parts"
        assert len(car["parts"]) == len(CAR_PARTS), (
            f"Level {level}: expected {len(CAR_PARTS)} parts, "
            f"got {len(car['parts'])}"
        )


# ---- Cycle 4: level 5 rival loading ----

def test_create_ghost_level_5():
    """Level 5 returns Tortoise rival car."""
    from engine.ghost import create_ghost

    car = create_ghost(5)
    assert car["CAR_NAME"] == "Tortoise"
    assert car["CAR_COLOR"] == "#27ae60"
    assert "parts" in car
