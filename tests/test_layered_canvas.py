"""Tests for T2.3: Layered canvas infrastructure + data enrichment module."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestDataEnrichmentJs:
    """viewer/js/data-enrichment.js exists and contains expected functions."""

    def test_file_exists(self):
        js = PROJECT_ROOT / "viewer" / "js" / "data-enrichment.js"
        assert js.exists(), "viewer/js/data-enrichment.js must exist"

    def test_has_enrich_function(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "data-enrichment.js").read_text()
        assert "function enrichReplayData(" in js

    def test_computes_headings_when_missing(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "data-enrichment.js").read_text()
        assert "track_headings" in js
        assert "Math.atan2" in js

    def test_computes_curvatures_when_missing(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "data-enrichment.js").read_text()
        assert "track_curvatures" in js

    def test_computes_distances_when_missing(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "data-enrichment.js").read_text()
        assert "_distances" in js

    def test_computes_normals_when_missing(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "data-enrichment.js").read_text()
        assert "_normals" in js

    def test_guards_existing_data(self):
        """Should not overwrite fields that already exist."""
        js = (PROJECT_ROOT / "viewer" / "js" / "data-enrichment.js").read_text()
        # Each computation block should check if the field already exists
        assert js.count("if (!replay.") >= 3, "Should guard at least headings, curvatures, distances"


class TestViewerShellThreeCanvases:
    """viewer/viewer.html shell has three stacked canvases."""

    def test_has_track_bg_canvas(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert 'id="trackBg"' in shell

    def test_has_car_layer_canvas(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert 'id="carLayer"' in shell

    def test_has_overlay_layer_canvas(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert 'id="overlayLayer"' in shell

    def test_no_old_single_canvas(self):
        """Old single canvas id='track' should be replaced."""
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert 'id="track"' not in shell

    def test_canvases_stack_via_css(self):
        """CSS should position canvases absolutely within container."""
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert ".track-container canvas" in shell
        assert "position: absolute" in shell

    def test_has_data_enrichment_inject(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "<!-- INJECT:js/data-enrichment.js -->" in shell

    def test_has_main_js_inject(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "<!-- INJECT:js/main.js -->" in shell

    def test_enrichment_before_main(self):
        """data-enrichment.js must be injected before main.js."""
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        enrich_pos = shell.index("INJECT:js/data-enrichment.js")
        main_pos = shell.index("INJECT:js/main.js")
        assert enrich_pos < main_pos


class TestMainJsRefactored:
    """viewer/js/main.js has layered rendering and worldToScreen."""

    def test_has_world_to_screen(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "function worldToScreen(" in js

    def test_has_render_background(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "function renderBackground()" in js

    def test_has_render_cars(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "function renderCars()" in js

    def test_has_render_overlay(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "function renderOverlay()" in js

    def test_render_calls_sub_renderers(self):
        """render() should call renderCars and renderOverlay, not draw track."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        # Find the render() function body
        render_idx = js.index("function render()")
        render_body = js[render_idx:render_idx + 400]
        assert "renderCars()" in render_body
        assert "renderOverlay()" in render_body

    def test_no_old_single_canvas_ref(self):
        """Should not reference old 'track' canvas id."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "getElementById('track')" not in js

    def test_has_three_canvas_refs(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "trackBg" in js
        assert "carLayer" in js
        assert "overlayLayer" in js

    def test_has_camera_object(self):
        """Camera state exists in main.js or camera.js (cameraSystem)."""
        main_js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        cam_js_path = PROJECT_ROOT / "viewer" / "js" / "camera.js"
        cam_js = cam_js_path.read_text() if cam_js_path.exists() else ""
        has_camera = "const camera" in main_js or "let camera" in main_js
        has_camera_system = "cameraSystem" in cam_js
        assert has_camera or has_camera_system

    def test_calls_enrich_in_load(self):
        """loadReplay should call enrichReplayData."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "enrichReplayData" in js

    def test_render_background_called_on_load(self):
        """renderBackground should be called in loadReplay."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        load_idx = js.index("function loadReplay(")
        # Find the next function definition to scope the search
        next_fn = js.find("\nfunction ", load_idx + 1)
        load_body = js[load_idx:next_fn] if next_fn > 0 else js[load_idx:]
        assert "renderBackground()" in load_body

    def test_under_400_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        lines = js.strip().split("\n")
        assert len(lines) < 400, f"main.js is {len(lines)} lines, must be < 400"


class TestBuildWithLayeredCanvas:
    """Built viewer.html includes all layers correctly."""

    def test_build_succeeds(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_built_has_enrich_function(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "function enrichReplayData(" in out

    def test_built_has_world_to_screen(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "function worldToScreen(" in out

    def test_built_has_three_canvases(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert 'id="trackBg"' in out
        assert 'id="carLayer"' in out
        assert 'id="overlayLayer"' in out

    def test_built_has_no_inject_markers(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in out

    def test_built_has_two_script_tags(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert out.count("<script>") >= 2, "Should have at least 2 inlined script blocks"

    def test_built_enrichment_before_main(self):
        """enrichReplayData should appear before worldToScreen in built output."""
        out = (PROJECT_ROOT / "viewer.html").read_text()
        enrich_pos = out.index("function enrichReplayData(")
        main_pos = out.index("function worldToScreen(")
        assert enrich_pos < main_pos

    def test_built_playback_controls_present(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "togglePlay" in out
        assert "setSpeed" in out
        assert 'id="scrubber"' in out
