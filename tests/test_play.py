"""Tests for play.py — track selection flags (T1.6)."""

import os
import sys
import subprocess

import pytest

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PLAY_PY = os.path.join(PROJECT_ROOT, "play.py")

pytestmark = pytest.mark.integration


# ── Cycle 1: --list-tracks ──────────────────────────────────────────────────

class TestListTracks:
    """--list-tracks prints all 20 tracks and exits."""

    def test_list_tracks_exits_zero(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--list-tracks"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0

    def test_list_tracks_shows_20_tracks(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--list-tracks"],
            capture_output=True, text=True,
        )
        from tracks import TRACKS
        for key in TRACKS:
            assert key in result.stdout.lower(), f"Track '{key}' missing from output"

    def test_list_tracks_shows_country(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--list-tracks"],
            capture_output=True, text=True,
        )
        assert "Italy" in result.stdout  # Monza

    def test_list_tracks_shows_character(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--list-tracks"],
            capture_output=True, text=True,
        )
        assert "power" in result.stdout.lower()

    def test_list_tracks_shows_count(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--list-tracks"],
            capture_output=True, text=True,
        )
        assert "20 tracks available" in result.stdout


# ── Cycle 2: --track NAME runs on named track ──────────────────────────────

class TestTrackSelection:
    """--track NAME passes track_name to run_race."""

    def test_track_flag_in_help(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--help"],
            capture_output=True, text=True,
        )
        assert "--track" in result.stdout

    def test_track_monza_runs(self):
        """python play.py --track monza should run and mention Monza."""
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--track", "monza", "--no-browser",
             "--laps", "1", "--output", "/tmp/npcrace_test_replay.json"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        # Should mention the track name somewhere in output
        assert "monza" in result.stdout.lower() or "Monza" in result.stdout


# ── Cycle 3: --track random picks a random track ───────────────────────────

class TestTrackRandom:
    """--track random picks a random track."""

    def test_track_random_runs(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--track", "random", "--no-browser",
             "--laps", "1", "--output", "/tmp/npcrace_test_replay.json"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0

    def test_track_random_prints_selection(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--track", "random", "--no-browser",
             "--laps", "1", "--output", "/tmp/npcrace_test_replay.json"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        assert "random track selected" in result.stdout.lower()


# ── Cycle 4: invalid --track gives clear error ─────────────────────────────

class TestTrackInvalid:
    """Invalid --track name gives clear error."""

    def test_invalid_track_name_error(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--track", "nonexistent_track_xyz"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode != 0

    def test_invalid_track_lists_available(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--track", "nonexistent_track_xyz"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        assert "available tracks" in result.stdout.lower()

    def test_invalid_track_mentions_name(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--track", "fakecircuit"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        output = result.stdout + result.stderr
        assert "fakecircuit" in output.lower()


# ── Cycle 5: --track ignores --seed; --seed alone still works ──────────────

class TestSeedInteraction:
    """--track ignores --seed; --seed alone still works procedurally."""

    def test_seed_alone_still_works(self):
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--seed", "99", "--no-browser",
             "--laps", "1", "--output", "/tmp/npcrace_test_replay.json"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0

    def test_track_with_seed_ignores_seed(self):
        """When --track is given, --seed is ignored (no error)."""
        result = subprocess.run(
            [sys.executable, PLAY_PY, "--track", "monza", "--seed", "99",
             "--no-browser", "--laps", "1", "--output", "/tmp/npcrace_test_replay.json"],
            capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        assert result.returncode == 0
        # Should note seed is being ignored
        output = result.stdout.lower()
        assert "ignor" in output or "monza" in output
