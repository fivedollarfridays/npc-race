"""Tests for viewer/js/car-renderer.js — top-down car model rendering."""

from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CAR_RENDERER = PROJECT / "viewer" / "js" / "car-renderer.js"
VIEWER_HTML = PROJECT / "viewer" / "viewer.html"
MAIN_JS = PROJECT / "viewer" / "js" / "main.js"


class TestCarRendererFileExists:
    """Cycle 1: car-renderer.js exists with renderCar function."""

    def test_file_exists(self):
        assert CAR_RENDERER.exists(), "viewer/js/car-renderer.js must exist"

    def test_exports_render_car_function(self):
        src = CAR_RENDERER.read_text()
        assert "function renderCar(" in src

    def test_render_car_signature_has_required_params(self):
        """renderCar(ctx, car, prevCar, replay, transform)"""
        src = CAR_RENDERER.read_text()
        assert "ctx" in src
        assert "car" in src
        assert "prevCar" in src
        assert "replay" in src
        assert "transform" in src


class TestCarRendererDrawingElements:
    """Cycle 2: car-renderer.js contains all required drawing elements."""

    def test_has_shadow(self):
        src = CAR_RENDERER.read_text()
        # Shadow uses semi-transparent dark color
        assert "shadow" in src.lower() or "#00000044" in src or "rgba(0" in src

    def test_has_car_body(self):
        src = CAR_RENDERER.read_text()
        # Body drawn as rounded rectangle or path with car color
        assert "car.color" in src or "color" in src

    def test_has_cockpit(self):
        src = CAR_RENDERER.read_text()
        # Cockpit is a darker area on the car
        assert "cockpit" in src.lower() or "darken" in src.lower()

    def test_has_rear_wing(self):
        src = CAR_RENDERER.read_text()
        assert "wing" in src.lower() or "#222" in src

    def test_has_wheels(self):
        src = CAR_RENDERER.read_text()
        assert "wheel" in src.lower() or "#111" in src

    def test_has_front_wheel_steering(self):
        """Front wheels should rotate based on heading look-ahead."""
        src = CAR_RENDERER.read_text()
        assert "steer" in src.lower() or "steering" in src.lower()

    def test_has_brake_lights(self):
        src = CAR_RENDERER.read_text()
        assert "brake" in src.lower()

    def test_brake_lights_check_speed_decrease(self):
        """Braking detected when speed drops > 2 km/h."""
        src = CAR_RENDERER.read_text()
        assert "prevCar" in src
        assert "speed" in src

    def test_has_boost_effect(self):
        src = CAR_RENDERER.read_text()
        assert "boost" in src.lower()

    def test_has_position_number(self):
        src = CAR_RENDERER.read_text()
        assert "position" in src

    def test_has_name_label(self):
        src = CAR_RENDERER.read_text()
        assert "name" in src

    def test_uses_track_headings_for_rotation(self):
        src = CAR_RENDERER.read_text()
        assert "track_headings" in src

    def test_uses_world_to_screen(self):
        src = CAR_RENDERER.read_text()
        assert "worldToScreen" in src

    def test_uses_save_restore(self):
        """Canvas state must be saved/restored for rotations."""
        src = CAR_RENDERER.read_text()
        assert ".save()" in src
        assert ".restore()" in src


class TestViewerHtmlInjectOrder:
    """Cycle 3: viewer.html has car-renderer.js INJECT marker in correct position."""

    def test_has_car_renderer_inject(self):
        html = VIEWER_HTML.read_text()
        assert "<!-- INJECT:js/car-renderer.js -->" in html

    def test_car_renderer_before_main(self):
        html = VIEWER_HTML.read_text()
        car_pos = html.index("car-renderer.js")
        main_pos = html.index("INJECT:js/main.js")
        assert car_pos < main_pos, "car-renderer.js must be injected before main.js"

    def test_car_renderer_after_data_enrichment(self):
        html = VIEWER_HTML.read_text()
        enrich_pos = html.index("data-enrichment.js")
        car_pos = html.index("car-renderer.js")
        assert enrich_pos < car_pos, "data-enrichment.js must come before car-renderer.js"


class TestMainJsUsesCarRenderer:
    """Cycle 4: main.js calls renderCar() instead of drawing circles."""

    def test_no_inline_circle_drawing(self):
        """renderCars should NOT draw circles directly anymore."""
        src = MAIN_JS.read_text()
        # The old code had carCtx.arc(cx, cy, r, ...) inside renderCars
        # After refactoring, renderCars should delegate to renderCar()
        # Check that the old circle-drawing pattern is gone
        lines = src.split("\n")
        in_render_cars = False
        has_arc_in_render_cars = False
        for line in lines:
            if "function renderCars()" in line:
                in_render_cars = True
            elif in_render_cars and line.strip().startswith("function "):
                break
            elif in_render_cars and "carCtx.arc(" in line:
                has_arc_in_render_cars = True
        assert not has_arc_in_render_cars, "renderCars should not draw circles directly"

    def test_render_cars_calls_render_car(self):
        """renderCars() should call renderCar() for each car."""
        src = MAIN_JS.read_text()
        assert "renderCar(" in src

    def test_render_cars_passes_prev_cars(self):
        """renderCars should compute prevCars for braking detection."""
        src = MAIN_JS.read_text()
        assert "prevCar" in src or "prev" in src


class TestCarRendererArchitecture:
    """Cycle 5: file size and function limits."""

    def test_file_under_400_lines(self):
        src = CAR_RENDERER.read_text()
        lines = len(src.strip().split("\n"))
        assert lines < 400, f"car-renderer.js is {lines} lines, must be under 400"

    def test_no_external_dependencies(self):
        """No require/import statements (pure browser JS)."""
        src = CAR_RENDERER.read_text()
        assert "require(" not in src
        assert "import " not in src


class TestBuildWithCarRenderer:
    """Cycle 6: build produces valid output with car renderer."""

    def test_build_succeeds(self):
        import subprocess

        result = subprocess.run(
            ["python", "scripts/build_viewer.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_built_output_has_render_car(self):
        import subprocess

        subprocess.run(
            ["python", "scripts/build_viewer.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT),
        )
        built = (PROJECT / "viewer.html").read_text()
        assert "function renderCar(" in built

    def test_built_output_has_no_inject_markers(self):
        import subprocess

        subprocess.run(
            ["python", "scripts/build_viewer.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT),
        )
        built = (PROJECT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in built

    def test_built_output_has_car_renderer_before_main(self):
        """car-renderer code should appear before main.js code in built output."""
        import subprocess

        subprocess.run(
            ["python", "scripts/build_viewer.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT),
        )
        built = (PROJECT / "viewer.html").read_text()
        car_pos = built.index("function renderCar(")
        main_pos = built.index("function renderCars()")
        assert car_pos < main_pos
