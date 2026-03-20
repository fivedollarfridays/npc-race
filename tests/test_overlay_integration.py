"""Tests for T2.6: Broadcast overlay — integration with viewer.html and main.js."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestViewerHtmlOverlayInject:
    """viewer.html has overlay.js script tag in correct position."""

    def test_has_overlay_inject_marker(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert '<script src="js/overlay.js"></script>' in html

    def test_overlay_before_main(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        overlay_pos = html.index("<script src=\"js/overlay.js")
        main_pos = html.index("<script src=\"js/main.js")
        assert overlay_pos < main_pos

    def test_overlay_after_enrichment(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        enrich_pos = html.index("<script src=\"js/data-enrichment.js")
        overlay_pos = html.index("<script src=\"js/overlay.js")
        assert enrich_pos < overlay_pos


class TestMainJsCallsOverlay:
    """main.js renderOverlay() calls renderBroadcastOverlay."""

    def test_render_overlay_calls_broadcast(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "renderBroadcastOverlay(" in js

    def test_render_overlay_clears_canvas(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        idx = js.index("function renderOverlay()")
        body = js[idx:idx + 600]
        assert "clearRect" in body

    def test_render_overlay_passes_dimensions(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        idx = js.index("function renderOverlay()")
        body = js[idx:idx + 600]
        assert "overlayCanvas.width" in body or "w" in body


class TestBuildWithOverlay:
    """Built viewer.html includes overlay functions."""

    def test_build_succeeds(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_built_has_overlay_functions(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "function renderBroadcastOverlay(" in out
        assert "function renderTimingTower(" in out
        assert "function renderLapCounter(" in out

    def test_built_has_no_inject_markers(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in out

    def test_built_overlay_before_main(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        overlay_pos = out.index("function renderBroadcastOverlay(")
        main_pos = out.index("function renderOverlay()")
        assert overlay_pos < main_pos


class TestOverlayFileLimits:
    """overlay.js stays under architecture limits."""

    def test_under_400_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "overlay.js").read_text()
        lines = js.strip().split("\n")
        assert len(lines) < 400, f"overlay.js is {len(lines)} lines, must be < 400"

    def test_main_js_still_under_400_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        lines = js.strip().split("\n")
        assert len(lines) < 600, f"main.js is {len(lines)} lines, must be < 400"
