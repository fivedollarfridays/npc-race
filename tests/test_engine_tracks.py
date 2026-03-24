"""Tests for engine track integration (T1.5).

Verifies that run_race() can use named track presets from
the tracks/ package, with proper fallback to procedural generation.
"""

import json
import os
import tempfile

import pytest

from tracks import get_track
from engine.race_runner import run_race

pytestmark = pytest.mark.smoke


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _car_dir():
    """Return the path to the cars/ directory."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "cars")


# ---------------------------------------------------------------------------
# Cycle 1: Named track loads correct control points
# ---------------------------------------------------------------------------

class TestNamedTrackIntegration:
    """run_race(track_name='monza') should use Monza control points."""

    def test_run_race_with_monza_completes(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            results = run_race(
                car_dir=_car_dir(), track_name="monza", laps=1, output=out,
            )
            assert len(results) >= 2
            assert any(r["finished"] for r in results)
        finally:
            os.unlink(out)

    def test_run_race_monza_replay_has_track_name(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            run_race(car_dir=_car_dir(), track_name="monza", laps=1, output=out)
            with open(out) as f:
                replay = json.load(f)
            assert replay["track_name"] == "monza"
        finally:
            os.unlink(out)


# ---------------------------------------------------------------------------
# Cycle 2: Track's laps_default used when laps not specified
# ---------------------------------------------------------------------------

class TestLapsDefault:
    """When laps is not specified, use the track's laps_default."""

    @pytest.mark.integration
    def test_laps_default_from_track(self):
        monza = get_track("monza")
        expected_laps = monza["laps_default"]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            run_race(car_dir=_car_dir(), track_name="monza", output=out)
            with open(out) as f:
                replay = json.load(f)
            assert replay["laps"] == expected_laps
        finally:
            os.unlink(out)


# ---------------------------------------------------------------------------
# Cycle 3: Explicit laps overrides track default
# ---------------------------------------------------------------------------

class TestExplicitLapsOverride:
    """Explicit laps= should override track's laps_default."""

    def test_explicit_laps_overrides_default(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            run_race(
                car_dir=_car_dir(), track_name="monza", laps=2, output=out,
            )
            with open(out) as f:
                replay = json.load(f)
            assert replay["laps"] == 2
        finally:
            os.unlink(out)


# ---------------------------------------------------------------------------
# Cycle 4: Procedural generation fallback
# ---------------------------------------------------------------------------

class TestProceduralFallback:
    """No track_name should fall back to procedural generation."""

    def test_run_race_no_track_name_still_works(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            results = run_race(car_dir=_car_dir(), laps=1, output=out)
            assert len(results) >= 2
            assert any(r["finished"] for r in results)
        finally:
            os.unlink(out)

    def test_procedural_replay_track_name_is_none(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            run_race(car_dir=_car_dir(), laps=1, output=out)
            with open(out) as f:
                replay = json.load(f)
            assert replay["track_name"] is None
        finally:
            os.unlink(out)

    def test_procedural_fallback_uses_default_laps(self):
        """When no track_name and no explicit laps, use default of 3."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            run_race(car_dir=_car_dir(), output=out)
            with open(out) as f:
                replay = json.load(f)
            assert replay["laps"] == 3
        finally:
            os.unlink(out)


# ---------------------------------------------------------------------------
# Cycle 5: track_name in replay JSON
# ---------------------------------------------------------------------------

class TestReplayTrackName:
    """Replay JSON should always include track_name field."""

    def test_replay_has_track_name_key(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            run_race(car_dir=_car_dir(), track_name="monza", laps=1, output=out)
            with open(out) as f:
                replay = json.load(f)
            assert "track_name" in replay
        finally:
            os.unlink(out)


# ---------------------------------------------------------------------------
# Cycle 6: Invalid track_name raises clear error
# ---------------------------------------------------------------------------

class TestInvalidTrackName:
    """Invalid track_name should raise a clear error."""

    def test_invalid_track_name_raises_key_error(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            with pytest.raises(KeyError, match="nonexistent_track"):
                run_race(
                    car_dir=_car_dir(), track_name="nonexistent_track",
                    laps=1, output=out,
                )
        finally:
            if os.path.exists(out):
                os.unlink(out)

    def test_error_message_is_helpful(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            out = f.name
        try:
            with pytest.raises(KeyError):
                run_race(
                    car_dir=_car_dir(), track_name="not_a_track",
                    laps=1, output=out,
                )
        finally:
            if os.path.exists(out):
                os.unlink(out)
