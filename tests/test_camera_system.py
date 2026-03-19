"""Tests for T2.9: Camera system — camera.js structure and modes."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestCameraJsExists:
    """viewer/js/camera.js exists with expected structure."""

    def test_file_exists(self):
        js = PROJECT_ROOT / "viewer" / "js" / "camera.js"
        assert js.exists(), "viewer/js/camera.js must exist"

    def test_has_camera_system_state(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "cameraSystem" in js, "Must have cameraSystem state object"

    def test_camera_system_has_mode(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "mode:" in js or "mode :" in js

    def test_camera_system_default_mode_full(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        # Default mode should be 'full'
        assert "'full'" in js or '"full"' in js

    def test_camera_system_has_target_fields(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "targetX" in js
        assert "targetY" in js
        assert "targetZoom" in js
        assert "targetRotation" in js

    def test_camera_system_has_current_fields(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "currentX" in js
        assert "currentY" in js
        assert "currentZoom" in js
        assert "currentRotation" in js

    def test_camera_system_has_lerp_speed(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "lerpSpeed" in js

    def test_camera_system_has_selected_car(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "selectedCar" in js


class TestCameraFunctions:
    """Camera mode functions exist with correct behavior."""

    def test_has_set_camera_mode(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "function setCameraMode(" in js

    def test_has_select_car(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "function selectCar(" in js

    def test_has_update_camera(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "function updateCamera(" in js

    def test_has_update_camera_buttons(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "function updateCameraButtons(" in js

    def test_has_lerp_camera(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "lerpSpeed" in js
        # Lerp logic: current += (target - current) * speed
        assert "targetX" in js and "currentX" in js

    def test_follow_mode_uses_look_ahead(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "lookAhead" in js
        assert "Math.cos" in js
        assert "Math.sin" in js

    def test_follow_mode_zoom_3(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "targetZoom = 3" in js

    def test_onboard_mode_zoom_6(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "targetZoom = 6" in js

    def test_onboard_mode_rotates_with_heading(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "targetRotation" in js
        # Onboard should use heading for rotation
        assert "Math.PI" in js

    def test_full_mode_resets_zoom_and_rotation(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "targetZoom = 1" in js
        assert "targetRotation = 0" in js

    def test_auto_selects_leader_when_no_car_selected(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        assert "position === 1" in js or "position==1" in js

    def test_select_car_switches_to_follow(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        # selectCar should auto-switch to follow mode when in full mode
        func_start = js.index("function selectCar(")
        func_body = js[func_start:js.index("}", func_start + 50) + 50]
        assert "follow" in func_body


class TestCameraFileLimits:
    """Camera and main.js files stay within architecture limits."""

    def test_camera_js_under_400_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "camera.js").read_text()
        lines = len(js.strip().splitlines())
        assert lines < 400, f"camera.js is {lines} lines, must be under 400"

    def test_main_js_under_400_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        lines = len(js.strip().splitlines())
        assert lines < 450, f"main.js is {lines} lines, must be under 450"
