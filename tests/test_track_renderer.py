"""Tests for T2.4: Realistic track renderer."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestTrackRendererFileExists:
    """viewer/js/track-renderer.js exists and has renderTrack function."""

    def test_file_exists(self):
        js = PROJECT_ROOT / "viewer" / "js" / "track-renderer.js"
        assert js.exists(), "viewer/js/track-renderer.js must exist"

    def test_has_render_track_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        assert "function renderTrack(" in js

    def test_render_track_accepts_ctx_replay_transform(self):
        """renderTrack should accept (ctx, replay, transform) parameters."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        assert "renderTrack(ctx, replay, transform)" in js or \
               "renderTrack(ctx, replay, transform)" in js.replace(" ", "")

    def test_under_300_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        lines = js.strip().split("\n")
        assert len(lines) < 300, f"track-renderer.js is {len(lines)} lines, should be < 300"


class TestTrackRendererLayers:
    """Track renderer has all required visual layers."""

    def test_has_grass_background(self):
        """Should fill canvas with green grass color."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        # Should have a green fill for grass
        assert "#1a3a1a" in js or "1a3a1a" in js or "grass" in js.lower()
        assert "fillRect" in js

    def test_has_runoff_area(self):
        """Should draw wider stroke for run-off areas."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        # Run-off is drawn as wider track stroke in gray
        assert "3a3a3a" in js or "runoff" in js.lower() or "run-off" in js.lower() or "run_off" in js.lower()

    def test_has_asphalt_surface(self):
        """Should draw track surface with asphalt color."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        assert "252530" in js or "asphalt" in js.lower()

    def test_has_asphalt_texture(self):
        """Should create noise texture for asphalt (offscreen canvas or pattern)."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        # Should use createPattern or offscreen canvas for texture
        assert "createPattern" in js or "createElement" in js

    def test_has_white_edge_lines(self):
        """Should draw white edge lines using track normals."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        assert "_normals" in js
        assert "#ffffff" in js or "fff" in js.lower()

    def test_has_kerbs_at_corners(self):
        """Should draw red/white kerbs at high-curvature points."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        assert "track_curvatures" in js
        assert "cc0000" in js or "kerb" in js.lower()

    def test_has_racing_line(self):
        """Should draw faint dashed racing line."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        assert "setLineDash" in js

    def test_has_start_finish_line(self):
        """Should draw checkered start/finish pattern."""
        js = (PROJECT_ROOT / "viewer" / "js" / "track-renderer.js").read_text()
        # Should have checkered pattern logic
        assert "checker" in js.lower() or ("black" in js.lower() and "white" in js.lower())


class TestViewerShellInjectOrder:
    """viewer/viewer.html has track-renderer.js injected in correct order."""

    def test_has_track_renderer_inject(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert '<script src="js/track-renderer.js"></script>' in shell

    def test_inject_order_enrichment_before_renderer(self):
        """data-enrichment.js must come before track-renderer.js."""
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        enrich_pos = shell.index("<script src=\"js/data-enrichment.js")
        renderer_pos = shell.index("<script src=\"js/track-renderer.js")
        assert enrich_pos < renderer_pos

    def test_inject_order_renderer_before_main(self):
        """track-renderer.js must come before main.js."""
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        renderer_pos = shell.index("<script src=\"js/track-renderer.js")
        main_pos = shell.index("<script src=\"js/main.js")
        assert renderer_pos < main_pos


class TestMainJsCallsRenderTrack:
    """main.js renderBackground() delegates to renderTrack()."""

    def test_render_background_calls_render_track(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        bg_idx = js.index("function renderBackground()")
        # Find next function to scope search
        next_fn = js.find("\nfunction ", bg_idx + 1)
        bg_body = js[bg_idx:next_fn] if next_fn > 0 else js[bg_idx:]
        assert "renderTrack(" in bg_body

    def test_render_background_passes_transform(self):
        """Should pass scale, ox, oy to renderTrack."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        bg_idx = js.index("function renderBackground()")
        next_fn = js.find("\nfunction ", bg_idx + 1)
        bg_body = js[bg_idx:next_fn] if next_fn > 0 else js[bg_idx:]
        assert "_scale" in bg_body or "scale" in bg_body

    def test_no_old_track_drawing_in_render_background(self):
        """Old inline track drawing code should be removed from renderBackground."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        bg_idx = js.index("function renderBackground()")
        next_fn = js.find("\nfunction ", bg_idx + 1)
        bg_body = js[bg_idx:next_fn] if next_fn > 0 else js[bg_idx:]
        # Old code had direct track drawing with strokeStyle '#1a1a2a'
        assert "#1a1a2a" not in bg_body, "Old track border drawing should be removed"


class TestBuildWithTrackRenderer:
    """Built viewer.html includes track-renderer.js correctly."""

    def test_build_succeeds(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_built_has_render_track(self):
        # Rebuild first
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "function renderTrack(" in out

    def test_built_has_three_script_blocks(self):
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert out.count("<script>") >= 3, "Should have at least 3 inlined script blocks"

    def test_built_render_track_before_main(self):
        """renderTrack function should appear before renderBackground in built output."""
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        out = (PROJECT_ROOT / "viewer.html").read_text()
        rt_pos = out.index("function renderTrack(")
        rb_pos = out.index("function renderBackground()")
        assert rt_pos < rb_pos, "renderTrack must be defined before renderBackground calls it"

    def test_built_no_inject_markers(self):
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        )
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in out
