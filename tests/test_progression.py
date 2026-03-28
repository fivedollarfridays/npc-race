"""Tests for player progression tracking."""

import pytest


@pytest.fixture()
def progress_file(tmp_path):
    """Return path to a temporary progress.json file."""
    return str(tmp_path / "progress.json")


# --- Cycle 1: Default progress ---

def test_default_progress_is_rookie(progress_file):
    """New player with no progress file should be rookie tier."""
    from cli.progression import _load_progress

    data = _load_progress(progress_file)
    assert data["tier"] == "rookie"
    assert data["ghost_completed"] == {}
    assert data["races_won"] == 0
    assert data["tracks_completed"] == []


def test_save_and_load_roundtrip(progress_file):
    """Saving and loading progress should preserve data."""
    from cli.progression import _load_progress, _save_progress

    data = {"ghost_completed": {"monza": 3}, "tier": "midfield",
            "races_won": 5, "tracks_completed": ["monza"]}
    _save_progress(data, progress_file)
    loaded = _load_progress(progress_file)
    assert loaded == data


# --- Cycle 2: Ghost completion recording ---

def test_ghost_completion_recorded(progress_file):
    """Recording ghost L3 on monza stores it in ghost_completed."""
    from cli.progression import record_ghost_completion

    data = record_ghost_completion("monza", 3, progress_file)
    assert data["ghost_completed"]["monza"] == 3


def test_ghost_completion_only_upgrades(progress_file):
    """Ghost level only updates if higher than current."""
    from cli.progression import record_ghost_completion

    record_ghost_completion("monza", 3, progress_file)
    data = record_ghost_completion("monza", 2, progress_file)
    assert data["ghost_completed"]["monza"] == 3  # stays at 3


# --- Cycle 3: Ghost L5 unlocks midfield ---

def test_ghost_level_5_unlocks_midfield(progress_file):
    """Beating Ghost Level 5 on any track upgrades rookie to midfield."""
    from cli.progression import record_ghost_completion

    data = record_ghost_completion("monza", 5, progress_file)
    assert data["tier"] == "midfield"


def test_ghost_level_4_stays_rookie(progress_file):
    """Ghost level 4 is not enough to unlock midfield."""
    from cli.progression import record_ghost_completion

    data = record_ghost_completion("monza", 4, progress_file)
    assert data["tier"] == "rookie"


def test_ghost_optional_after_first_track(progress_file):
    """Once L5 beaten on one track, other tracks don't need L5."""
    from cli.progression import record_ghost_completion

    record_ghost_completion("monza", 5, progress_file)
    data = record_ghost_completion("silverstone", 2, progress_file)
    assert data["tier"] == "midfield"  # still midfield
    assert data["ghost_completed"]["silverstone"] == 2


# --- Cycle 4: Race win upgrades tier ---

def test_race_win_midfield_upgrades_to_front(progress_file):
    """Winning at midfield tier upgrades to front."""
    from cli.progression import record_ghost_completion, record_race_win

    # First unlock midfield
    record_ghost_completion("monza", 5, progress_file)
    data = record_race_win("midfield", progress_file)
    assert data["tier"] == "front"
    assert data["races_won"] == 1


def test_race_win_front_upgrades_to_full(progress_file):
    """Winning at front tier upgrades to full."""
    from cli.progression import _save_progress, record_race_win

    _save_progress(
        {"ghost_completed": {"monza": 5}, "tier": "front",
         "races_won": 1, "tracks_completed": []},
        progress_file,
    )
    data = record_race_win("front", progress_file)
    assert data["tier"] == "full"
    assert data["races_won"] == 2


def test_race_win_rookie_no_upgrade(progress_file):
    """Winning at rookie tier does NOT upgrade (need ghost completion)."""
    from cli.progression import record_race_win

    data = record_race_win("rookie", progress_file)
    assert data["tier"] == "rookie"
    assert data["races_won"] == 1


# --- Cycle 5: Progress summary ---

def test_progress_summary_format(progress_file):
    """Summary includes tier, ghost levels, and race wins."""
    from cli.progression import record_ghost_completion, get_progress_summary

    record_ghost_completion("monza", 3, progress_file)
    summary = get_progress_summary(progress_file)
    assert "ROOKIE" in summary
    assert "monza: L3" in summary
    assert "Race wins: 0" in summary


def test_progress_summary_empty(progress_file):
    """Summary for new player shows defaults."""
    from cli.progression import get_progress_summary

    summary = get_progress_summary(progress_file)
    assert "ROOKIE" in summary
    assert "none" in summary
    assert "Race wins: 0" in summary


# --- Cycle 6: Reset progress ---

def test_reset_progress(progress_file):
    """Reset clears everything back to defaults."""
    from cli.progression import (
        _load_progress, record_ghost_completion, reset_progress,
    )

    record_ghost_completion("monza", 5, progress_file)
    reset_progress(progress_file)
    data = _load_progress(progress_file)
    assert data["tier"] == "rookie"
    assert data["ghost_completed"] == {}
    assert data["races_won"] == 0


# --- Cycle 7: CLI progress command ---

def test_cmd_progress_shows_summary(progress_file, capsys, monkeypatch):
    """The progress CLI command prints the summary."""
    from cli.progression import record_ghost_completion
    from cli import progression as prog_mod

    record_ghost_completion("monza", 3, progress_file)
    monkeypatch.setattr(prog_mod, "DEFAULT_PROGRESS_PATH", progress_file)

    from cli.progression import cmd_progress

    class FakeArgs:
        pass

    result = cmd_progress(FakeArgs())
    assert result == 0
    captured = capsys.readouterr()
    assert "ROOKIE" in captured.out
    assert "monza: L3" in captured.out
