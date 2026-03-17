"""Tests for T2.9: Camera integration — HTML, main.js wiring, and build."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestViewerHtmlCameraIntegration:
    """viewer.html has camera INJECT marker and camera buttons."""

    def test_inject_marker_exists(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "<!-- INJECT:js/camera.js -->" in html

    def test_inject_marker_before_main(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        cam_pos = html.index("INJECT:js/camera.js")
        main_pos = html.index("INJECT:js/main.js")
        assert cam_pos < main_pos, "camera.js must be injected before main.js"

    def test_inject_marker_after_overlay(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        overlay_pos = html.index("INJECT:js/overlay.js")
        cam_pos = html.index("INJECT:js/camera.js")
        assert cam_pos > overlay_pos, "camera.js must be injected after overlay.js"

    def test_camera_buttons_exist(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert 'id="cam-full"' in html
        assert 'id="cam-follow"' in html
        assert 'id="cam-onboard"' in html

    def test_camera_buttons_have_class(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "cam-btn" in html

    def test_full_button_is_default_active(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        # The full track button should have active class by default
        full_btn_idx = html.index('id="cam-full"')
        btn_tag = html[html.rfind("<button", 0, full_btn_idx):full_btn_idx + 30]
        assert "active" in btn_tag

    def test_buttons_call_set_camera_mode(self):
        html = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "setCameraMode('full')" in html or 'setCameraMode("full")' in html
        assert "setCameraMode('follow')" in html or 'setCameraMode("follow")' in html
        assert "setCameraMode('onboard')" in html or 'setCameraMode("onboard")' in html


class TestMainJsCameraIntegration:
    """main.js integrates camera system into transform and tick loop."""

    def test_tick_calls_update_camera(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "updateCamera(" in js, "tick must call updateCamera"

    def test_tick_recomputes_transform_for_camera(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "computeTransform()" in js

    def test_tick_rerenders_background_for_camera(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "renderBackground()" in js

    def test_compute_transform_handles_camera_mode(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "cameraSystem" in js, "computeTransform must reference cameraSystem"

    def test_world_to_screen_applies_rotation(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "currentRotation" in js or "rotation" in js.lower()

    def test_keyboard_shortcuts_exist(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "keydown" in js, "Must have keydown listener"

    def test_keyboard_shortcut_t_for_full(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "'t'" in js.lower() or '"t"' in js.lower() or "'T'" in js

    def test_keyboard_shortcut_f_for_follow(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "'f'" in js.lower() or '"f"' in js.lower() or "'F'" in js

    def test_keyboard_shortcut_o_for_onboard(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "'o'" in js.lower() or '"o"' in js.lower() or "'O'" in js

    def test_keyboard_escape_returns_to_full(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "Escape" in js


class TestMainJsWorldToScreenRotation:
    """worldToScreen applies rotation transform for onboard cam."""

    def test_world_to_screen_uses_cos_sin(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        func_start = js.index("function worldToScreen(")
        func_end = js.index("\n}", func_start) + 2
        func_body = js[func_start:func_end]
        assert "cos" in func_body or "Math.cos" in func_body

    def test_world_to_screen_uses_canvas_center(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        func_start = js.index("function worldToScreen(")
        func_end = js.index("\n}", func_start) + 2
        func_body = js[func_start:func_end]
        assert "/ 2" in func_body


class TestOverlayClickSelection:
    """Overlay canvas click selects car from timing tower."""

    def test_overlay_click_handler_exists(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "overlayCanvas" in js
        assert "click" in js

    def test_click_handler_calls_select_car(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "selectCar(" in js


class TestBuildWithCamera:
    """Build output includes camera system correctly."""

    def test_build_succeeds(self):
        import subprocess
        result = subprocess.run(
            ["python", "scripts/build_viewer.py"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_built_html_has_camera_system(self):
        import subprocess
        subprocess.run(
            ["python", "scripts/build_viewer.py"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
        )
        built = (PROJECT_ROOT / "viewer.html").read_text()
        assert "cameraSystem" in built

    def test_built_html_has_set_camera_mode(self):
        built = (PROJECT_ROOT / "viewer.html").read_text()
        assert "setCameraMode" in built

    def test_built_html_has_camera_buttons(self):
        built = (PROJECT_ROOT / "viewer.html").read_text()
        assert 'id="cam-full"' in built
        assert 'id="cam-follow"' in built
        assert 'id="cam-onboard"' in built

    def test_built_html_no_inject_markers(self):
        built = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in built

    def test_built_html_camera_before_main(self):
        built = (PROJECT_ROOT / "viewer.html").read_text()
        cam_pos = built.index("cameraSystem")
        main_pos = built.index("updateCamera(replay, frame)")
        assert cam_pos < main_pos

    def test_built_html_has_keyboard_shortcuts(self):
        built = (PROJECT_ROOT / "viewer.html").read_text()
        assert "keydown" in built
        assert "Escape" in built
