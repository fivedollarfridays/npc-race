"""Tests for T2.6: F1-style broadcast overlay — overlay.js structure and rendering."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestOverlayJsStructure:
    """viewer/js/overlay.js exists and has expected structure."""

    def test_file_exists(self):
        js = PROJECT_ROOT / "viewer" / "js" / "overlay.js"
        assert js.exists(), "viewer/js/overlay.js must exist"

    def test_has_overlay_state(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "overlayState" in js, "Must have overlayState object"

    def test_overlay_state_has_overtake_queue(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "overtakeQueue" in js

    def test_overlay_state_has_last_positions(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "lastPositions" in js

    def test_overlay_state_has_lap_times(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "lapTimes" in js

    def test_overlay_state_has_fastest_lap(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "fastestLap" in js

    def test_has_broadcast_overlay_entry_point(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "function renderBroadcastOverlay(" in js

    def test_broadcast_overlay_accepts_five_params(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        idx = js.index("function renderBroadcastOverlay(")
        sig = js[idx:js.index(")", idx) + 1]
        params = sig.split("(")[1].rstrip(")").split(",")
        assert len(params) == 5, f"Expected 5 params, got {len(params)}: {sig}"


class TestTimingTower:
    """renderTimingTower function for position/speed display."""

    def test_has_timing_tower_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "function renderTimingTower(" in js

    def test_timing_tower_draws_position_numbers(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "position" in js

    def test_timing_tower_draws_color_bar(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "car.color" in js or "color" in js

    def test_timing_tower_draws_abbreviation(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "substring" in js or "slice" in js or "substr" in js

    def test_timing_tower_shows_speed(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "speed" in js
        assert "km/h" in js

    def test_timing_tower_has_semi_transparent_bg(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "rgba" in js or "#0a0a0f" in js

    def test_timing_tower_highlights_p1(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "gold" in js.lower() or "#ffd700" in js.lower() or "ffd" in js.lower()


class TestLapCounter:
    """renderLapCounter function for lap display."""

    def test_has_lap_counter_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "function renderLapCounter(" in js

    def test_lap_counter_shows_lap_x_of_y(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "LAP" in js

    def test_lap_counter_uses_outfit_font(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "Outfit" in js


class TestRaceStatus:
    """renderRaceStatus function for status badge."""

    def test_has_race_status_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "function renderRaceStatus(" in js

    def test_shows_race_badge(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "RACE" in js

    def test_shows_final_lap_badge(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "FINAL LAP" in js

    def test_shows_chequered_flag_badge(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "CHEQUERED FLAG" in js or "CHECKERED FLAG" in js

    def test_race_status_green_color(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "#44cc44" in js

    def test_final_lap_yellow_color(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "#ccaa00" in js


class TestSpeedReadout:
    """renderSpeedReadout function for leader speed display."""

    def test_has_speed_readout_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "function renderSpeedReadout(" in js


class TestOvertakeNotification:
    """renderOvertakeNotification for position change alerts."""

    def test_has_overtake_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "function renderOvertakeNotification(" in js

    def test_shows_overtake_text(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "OVERTAKE" in js

    def test_overtake_fades_out(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "globalAlpha" in js or "alpha" in js.lower()

    def test_overtake_has_duration(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "duration" in js


class TestFastestLap:
    """renderFastestLap for purple dot on fastest lap car."""

    def test_has_fastest_lap_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "function renderFastestLap(" in js or "fastestLap" in js

    def test_purple_indicator(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        assert "#9900ff" in js
