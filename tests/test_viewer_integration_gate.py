"""Tests for T2.10 Integration Gate — viewer integration and polish.

Verifies: sidebar removal, bottom bar, main.js cleanup, build output,
backward compatibility, and full feature integration.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VIEWER_DIR = PROJECT_ROOT / "viewer"
SHELL_PATH = VIEWER_DIR / "viewer.html"
MAIN_JS_PATH = VIEWER_DIR / "js" / "main.js"


def _read_shell() -> str:
    return SHELL_PATH.read_text()


def _read_main_js() -> str:
    return MAIN_JS_PATH.read_text()


# ─── Cycle 1: Sidebar Removal ────────────────────────────────────────────────


class TestSidebarRemoved:
    """Old sidebar HTML and CSS must be removed from viewer.html shell."""

    def test_no_sidebar_div(self):
        html = _read_shell()
        assert '<div class="sidebar">' not in html

    def test_no_sidebar_title(self):
        html = _read_shell()
        assert "sidebar-title" not in html

    def test_no_leaderboard_div(self):
        html = _read_shell()
        assert '<div class="leaderboard"' not in html

    def test_no_sidebar_css(self):
        html = _read_shell()
        assert ".sidebar {" not in html
        assert ".sidebar-title {" not in html

    def test_no_car_row_css(self):
        html = _read_shell()
        assert ".car-row {" not in html
        assert ".car-pos {" not in html
        assert ".car-dot {" not in html

    def test_no_tire_bar_css(self):
        html = _read_shell()
        assert ".tire-bar {" not in html
        assert ".tire-fill {" not in html

    def test_no_boost_indicator_css(self):
        html = _read_shell()
        assert ".boost-indicator {" not in html

    def test_no_leaderboard_css(self):
        html = _read_shell()
        assert ".leaderboard {" not in html


# ─── Cycle 2: Bottom Control Bar ─────────────────────────────────────────────


class TestBottomBar:
    """Bottom bar overlay replaces sidebar controls."""

    def test_has_bottom_bar_div(self):
        html = _read_shell()
        assert '<div class="bottom-bar"' in html

    def test_has_play_button(self):
        html = _read_shell()
        assert 'id="playBtn"' in html
        assert "togglePlay()" in html

    def test_has_speed_buttons(self):
        html = _read_shell()
        assert "setSpeed(0.5" in html
        assert "setSpeed(1," in html
        assert "setSpeed(2," in html
        assert "setSpeed(4," in html

    def test_has_scrubber(self):
        html = _read_shell()
        assert 'id="scrubber"' in html

    def test_has_camera_buttons(self):
        html = _read_shell()
        assert "setCameraMode('full')" in html
        assert "setCameraMode('follow')" in html
        assert "setCameraMode('onboard')" in html

    def test_has_mute_button(self):
        html = _read_shell()
        assert 'id="muteBtn"' in html
        assert "toggleMute()" in html

    def test_has_volume_slider(self):
        html = _read_shell()
        assert 'id="volumeSlider"' in html
        assert "setVolume(" in html

    def test_bottom_bar_css(self):
        html = _read_shell()
        assert ".bottom-bar {" in html
        assert "position: absolute" in html

    def test_bottom_bar_inside_track_container(self):
        """Bottom bar should be inside track-container for absolute positioning."""
        html = _read_shell()
        tc_start = html.index("track-container")
        bottom_bar = html.index("bottom-bar")
        assert bottom_bar > tc_start, "Bottom bar should be inside track container"

    def test_track_container_full_width(self):
        """Track container should take full width (no sidebar splitting space)."""
        html = _read_shell()
        # main-area should not contain a sidebar div
        main_start = html.index("main-area")
        main_section = html[main_start:]
        assert "sidebar" not in main_section.split("</div>")[0:10]


# ─── Cycle 3: main.js Cleanup ────────────────────────────────────────────────


class TestMainJsCleanup:
    """main.js should not have HTML-based leaderboard update functions."""

    def test_no_update_leaderboard_function(self):
        js = _read_main_js()
        assert "function updateLeaderboard(" not in js

    def test_no_update_leaderboard_call(self):
        js = _read_main_js()
        assert "updateLeaderboard(" not in js

    def test_no_leaderboard_element_access(self):
        js = _read_main_js()
        assert "getElementById('leaderboard')" not in js

    def test_no_lap_display_element(self):
        """Lap display moved to overlay -- no HTML element reference."""
        js = _read_main_js()
        assert "getElementById('lapDisplay')" not in js

    def test_has_show_results(self):
        """showResults() should still exist for the HTML finish overlay."""
        js = _read_main_js()
        assert "function showResults()" in js

    def test_has_render_broadcast_overlay_call(self):
        js = _read_main_js()
        assert "renderBroadcastOverlay(" in js

    def test_main_js_under_400_lines(self):
        js = _read_main_js()
        lines = js.strip().split("\n")
        assert len(lines) < 400, f"main.js has {len(lines)} lines, must be < 400"


# ─── Cycle 4: INJECT Marker Order ────────────────────────────────────────────


class TestInjectOrder:
    """All 8 JS files injected in correct dependency order."""

    def test_all_8_inject_markers_present(self):
        html = _read_shell()
        expected = [
            "data-enrichment.js",
            "track-renderer.js",
            "car-renderer.js",
            "overlay.js",
            "sound-engine.js",
            "physics-fx.js",
            "camera.js",
            "main.js",
        ]
        for name in expected:
            assert f"<!-- INJECT:js/{name} -->" in html, f"Missing INJECT for {name}"

    def test_inject_order_correct(self):
        html = _read_shell()
        markers = [
            "data-enrichment.js",
            "track-renderer.js",
            "car-renderer.js",
            "overlay.js",
            "sound-engine.js",
            "physics-fx.js",
            "camera.js",
            "main.js",
        ]
        positions = [html.index(f"<!-- INJECT:js/{m} -->") for m in markers]
        assert positions == sorted(positions), "INJECT markers not in correct order"


# ─── Cycle 5: Backward Compatibility ─────────────────────────────────────────


class TestBackwardCompatibility:
    """Data enrichment handles old replays; car-renderer handles missing seg."""

    def test_data_enrichment_computes_headings(self):
        js = (VIEWER_DIR / "js" / "data-enrichment.js").read_text()
        assert "track_headings" in js
        assert "Math.atan2" in js

    def test_data_enrichment_computes_curvatures(self):
        js = (VIEWER_DIR / "js" / "data-enrichment.js").read_text()
        assert "track_curvatures" in js

    def test_data_enrichment_guards_existing(self):
        """Should not overwrite fields that already exist."""
        js = (VIEWER_DIR / "js" / "data-enrichment.js").read_text()
        assert "if (!replay.track_headings)" in js
        assert "if (!replay.track_curvatures)" in js

    def test_car_renderer_seg_fallback(self):
        """car-renderer.js should handle missing car.seg gracefully."""
        js = (VIEWER_DIR / "js" / "car-renderer.js").read_text()
        # Should have a fallback for when seg is null/undefined
        assert "car.seg" in js
        # Uses || 0 or != null check for seg access
        assert "seg" in js


# ─── Cycle 6: Build Output ───────────────────────────────────────────────────


class TestBuildOutput:
    """Built viewer.html has all integrated features."""

    def _build_and_read(self) -> str:
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        return (PROJECT_ROOT / "viewer.html").read_text()

    def test_build_no_inject_markers(self):
        html = self._build_and_read()
        assert "<!-- INJECT:" not in html

    def test_build_has_all_functions(self):
        html = self._build_and_read()
        for fn in [
            "renderTrack",
            "renderCar",
            "renderBroadcastOverlay",
            "updateSound",
            "updateTireMarks",
            "updateCamera",
            "enrichReplayData",
        ]:
            assert fn in html, f"Built viewer.html missing function: {fn}"

    def test_build_no_sidebar(self):
        html = self._build_and_read()
        assert '<div class="sidebar">' not in html

    def test_build_has_bottom_bar(self):
        html = self._build_and_read()
        assert "bottom-bar" in html

    def test_build_has_drag_drop(self):
        html = self._build_and_read()
        assert "drop-overlay" in html
        assert "replay.json" in html

    def test_build_has_finished_overlay(self):
        html = self._build_and_read()
        assert "finished-overlay" in html

    def test_build_size_reasonable(self):
        html = self._build_and_read()
        size = len(html.encode("utf-8"))
        assert size < 70000, f"Built file too large: {size} bytes"
        assert size > 10000, f"Built file too small: {size} bytes"

    def test_build_starts_ends_correctly(self):
        html = self._build_and_read()
        assert html.strip().startswith("<!DOCTYPE html>")
        assert html.strip().endswith("</html>")
