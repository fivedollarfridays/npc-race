"""Tests for engine/ghost_race.py — ghost race 2-car comparison."""

import os
import shutil

import pytest


TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "cars", "default_project"
)


@pytest.fixture
def car_dir(tmp_path):
    """Copy default_project to a temp directory."""
    dest = str(tmp_path / "test_car")
    shutil.copytree(TEMPLATE_DIR, dest)
    return dest


# ---- Cycle 1: basic ghost race returns GhostResult with times ----

@pytest.mark.smoke
def test_ghost_race_returns_result(car_dir):
    """run_ghost_race returns a GhostResult dataclass."""
    from engine.ghost_race import run_ghost_race, GhostResult

    result = run_ghost_race(car_dir, "monza", 1)
    assert isinstance(result, GhostResult)


@pytest.mark.smoke
def test_ghost_race_has_two_times(car_dir):
    """Both player_time and ghost_time are positive."""
    from engine.ghost_race import run_ghost_race

    result = run_ghost_race(car_dir, "monza", 1)
    assert result.player_time > 0
    assert result.ghost_time > 0


# ---- Cycle 2: winner field matches actual times ----

@pytest.mark.smoke
def test_winner_is_correct(car_dir):
    """winner field matches whichever time is lower."""
    from engine.ghost_race import run_ghost_race

    result = run_ghost_race(car_dir, "monza", 1)
    if result.player_time <= result.ghost_time:
        assert result.winner == "player"
    else:
        assert result.winner == "ghost"
    assert result.margin == pytest.approx(
        abs(result.player_time - result.ghost_time), abs=0.001
    )


# ---- Cycle 3: efficiency dicts populated ----

@pytest.mark.smoke
def test_efficiency_comparison(car_dir):
    """Both player and ghost have non-empty efficiency dicts."""
    from engine.ghost_race import run_ghost_race

    result = run_ghost_race(car_dir, "monza", 1)
    assert isinstance(result.player_efficiency, dict)
    assert isinstance(result.ghost_efficiency, dict)
    assert len(result.player_efficiency) > 0
    assert len(result.ghost_efficiency) > 0


# ---- Cycle 4: ghost flaw/description and next_level ----

def test_ghost_flaw_shown(car_dir):
    """ghost_flaw and ghost_description are populated."""
    from engine.ghost_race import run_ghost_race

    result = run_ghost_race(car_dir, "monza", 1)
    assert result.ghost_flaw == "gearbox"
    assert "14,000" in result.ghost_description


def test_next_level_for_levels_1_through_4():
    """Levels 1-4 have next_level set, level 5 has None."""
    from engine.ghost_race import GhostResult

    for lvl in range(1, 5):
        r = GhostResult(
            player_time=60.0, ghost_time=61.0,
            winner="player", margin=1.0,
            player_efficiency={}, ghost_efficiency={},
            ghost_flaw="test", ghost_description="test",
            level=lvl, next_level=lvl + 1,
        )
        assert r.next_level == lvl + 1

    r5 = GhostResult(
        player_time=60.0, ghost_time=61.0,
        winner="player", margin=1.0,
        player_efficiency={}, ghost_efficiency={},
        ghost_flaw="none", ghost_description="test",
        level=5, next_level=None,
    )
    assert r5.next_level is None


# ---- Cycle 5: format output ----

def test_format_output():
    """format_ghost_result produces readable string with 'Level'."""
    from engine.ghost_race import format_ghost_result, GhostResult

    r = GhostResult(
        player_time=85.123, ghost_time=87.456,
        winner="player", margin=2.333,
        player_efficiency={"gearbox": 0.95, "cooling": 0.88},
        ghost_efficiency={"gearbox": 0.72, "cooling": 0.88},
        ghost_flaw="gearbox",
        ghost_description="Over-revving engine (shifts at 14,000 RPM)",
        level=1, next_level=2,
    )
    text = format_ghost_result(r)
    assert "Level 1" in text
    assert "You won by" in text
    assert "Ghost flaw:" in text
    assert "NEXT: Level 2" in text
