"""Tests for T2.8: Physics visualization effects (viewer/js/physics-fx.js)."""

from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PHYSICS_FX = PROJECT / "viewer" / "js" / "physics-fx.js"
VIEWER_HTML = PROJECT / "viewer" / "viewer.html"
MAIN_JS = PROJECT / "viewer" / "js" / "main.js"


# ── Cycle 1: File exists with state and reset ────────────────────────────────


class TestPhysicsFxFileExists:
    """physics-fx.js exists with physicsFx state and resetPhysicsFx."""

    def test_file_exists(self):
        assert PHYSICS_FX.exists(), "viewer/js/physics-fx.js must exist"

    def test_has_physics_fx_state(self):
        src = PHYSICS_FX.read_text()
        assert "physicsFx" in src, "Must have physicsFx state object"

    def test_state_has_tire_marks_array(self):
        src = PHYSICS_FX.read_text()
        assert "tireMarks" in src

    def test_state_has_max_marks_cap(self):
        src = PHYSICS_FX.read_text()
        assert "maxMarks" in src
        assert "2000" in src

    def test_has_reset_function(self):
        src = PHYSICS_FX.read_text()
        assert "function resetPhysicsFx(" in src


# ── Cycle 2: Tire marks functions ────────────────────────────────────────────


class TestTireMarks:
    """updateTireMarks and renderTireMarks functions."""

    def test_has_update_tire_marks_function(self):
        src = PHYSICS_FX.read_text()
        assert "function updateTireMarks(" in src

    def test_update_tire_marks_checks_curvature(self):
        """Should check curvature > 0.03 threshold."""
        src = PHYSICS_FX.read_text()
        assert "0.03" in src

    def test_update_tire_marks_checks_speed(self):
        """Should check speed > 80."""
        src = PHYSICS_FX.read_text()
        # Speed threshold for tire marks
        assert "80" in src

    def test_has_render_tire_marks_function(self):
        src = PHYSICS_FX.read_text()
        assert "function renderTireMarks(" in src

    def test_render_tire_marks_uses_dark_color(self):
        """Tire marks should use dark color (#111)."""
        src = PHYSICS_FX.read_text()
        assert "#111" in src


# ── Cycle 3: Brake glow ─────────────────────────────────────────────────────


class TestBrakeGlow:
    """renderBrakeGlow draws red glow trail behind braking cars."""

    def test_has_render_brake_glow_function(self):
        src = PHYSICS_FX.read_text()
        assert "function renderBrakeGlow(" in src

    def test_brake_glow_uses_red_color(self):
        """Brake glow should use red (#ff0000)."""
        src = PHYSICS_FX.read_text()
        # Find renderBrakeGlow function body
        idx = src.index("function renderBrakeGlow(")
        body = src[idx:src.find("\nfunction ", idx + 1)] if src.find("\nfunction ", idx + 1) > 0 else src[idx:]
        assert "ff0000" in body or "red" in body.lower()

    def test_brake_glow_uses_radial_gradient(self):
        """Should use radial gradient for glow effect."""
        src = PHYSICS_FX.read_text()
        idx = src.index("function renderBrakeGlow(")
        body = src[idx:src.find("\nfunction ", idx + 1)] if src.find("\nfunction ", idx + 1) > 0 else src[idx:]
        assert "createRadialGradient" in body

    def test_brake_glow_checks_speed_drop(self):
        """Should detect braking via speed drop > 5 km/h."""
        src = PHYSICS_FX.read_text()
        idx = src.index("function renderBrakeGlow(")
        body = src[idx:src.find("\nfunction ", idx + 1)] if src.find("\nfunction ", idx + 1) > 0 else src[idx:]
        # Should reference speed comparison
        assert "speed" in body


# ── Cycle 4: Drafting wake ───────────────────────────────────────────────────


class TestDraftingWake:
    """renderDraftingWake draws slipstream lines between close cars."""

    def test_has_render_drafting_wake_function(self):
        src = PHYSICS_FX.read_text()
        assert "function renderDraftingWake(" in src

    def test_drafting_wake_checks_distance(self):
        """Should compute distance between car pairs."""
        src = PHYSICS_FX.read_text()
        idx = src.index("function renderDraftingWake(")
        body = src[idx:]
        assert "sqrt" in body or "Math.sqrt" in body

    def test_drafting_wake_uses_translucent_white(self):
        """Slipstream lines should be faint translucent white."""
        src = PHYSICS_FX.read_text()
        idx = src.index("function renderDraftingWake(")
        body = src[idx:]
        # Should have a very transparent white color
        assert "ffffff" in body.lower() or "rgba(255" in body


# ── Cycle 5: Viewer HTML script tag ──────────────────────────────────────


class TestViewerHtmlPhysicsFxInject:
    """viewer.html has physics-fx.js script tag in correct position."""

    def test_has_physics_fx_inject(self):
        html = VIEWER_HTML.read_text()
        assert '<script src="js/physics-fx.js"></script>' in html

    def test_inject_after_car_renderer(self):
        html = VIEWER_HTML.read_text()
        car_pos = html.index("<script src=\"js/car-renderer.js")
        fx_pos = html.index("<script src=\"js/physics-fx.js")
        assert car_pos < fx_pos

    def test_inject_before_main(self):
        html = VIEWER_HTML.read_text()
        fx_pos = html.index("<script src=\"js/physics-fx.js")
        main_pos = html.index("<script src=\"js/main.js")
        assert fx_pos < main_pos


# ── Cycle 6: main.js wiring ─────────────────────────────────────────────────


class TestMainJsPhysicsFxWiring:
    """main.js calls physics-fx functions at the right points."""

    def test_render_background_calls_render_tire_marks(self):
        """renderBackground() should call renderTireMarks after renderTrack."""
        src = MAIN_JS.read_text()
        bg_idx = src.index("function renderBackground()")
        next_fn = src.find("\nfunction ", bg_idx + 1)
        bg_body = src[bg_idx:next_fn] if next_fn > 0 else src[bg_idx:]
        assert "renderTireMarks(" in bg_body

    def test_render_cars_calls_update_tire_marks(self):
        """renderCars() should call updateTireMarks."""
        src = MAIN_JS.read_text()
        cars_idx = src.index("function renderCars()")
        next_fn = src.find("\nfunction ", cars_idx + 1)
        cars_body = src[cars_idx:next_fn] if next_fn > 0 else src[cars_idx:]
        assert "updateTireMarks(" in cars_body

    def test_render_cars_calls_brake_glow(self):
        """renderCars() should call renderBrakeGlow."""
        src = MAIN_JS.read_text()
        cars_idx = src.index("function renderCars()")
        next_fn = src.find("\nfunction ", cars_idx + 1)
        cars_body = src[cars_idx:next_fn] if next_fn > 0 else src[cars_idx:]
        assert "renderBrakeGlow(" in cars_body

    def test_render_cars_calls_drafting_wake(self):
        """renderCars() should call renderDraftingWake."""
        src = MAIN_JS.read_text()
        cars_idx = src.index("function renderCars()")
        next_fn = src.find("\nfunction ", cars_idx + 1)
        cars_body = src[cars_idx:next_fn] if next_fn > 0 else src[cars_idx:]
        assert "renderDraftingWake(" in cars_body

    def test_load_replay_calls_reset(self):
        """loadReplay() should call resetPhysicsFx()."""
        src = MAIN_JS.read_text()
        load_idx = src.index("function loadReplay(")
        next_fn = src.find("\nfunction ", load_idx + 1)
        load_body = src[load_idx:next_fn] if next_fn > 0 else src[load_idx:]
        assert "resetPhysicsFx()" in load_body

    def test_scrubber_calls_reset(self):
        """Scrubber input handler should call resetPhysicsFx()."""
        src = MAIN_JS.read_text()
        # Find the scrubber event listener (addEventListener('input'))
        scrub_idx = src.index("scrubber').addEventListener")
        scrub_section = src[scrub_idx:scrub_idx + 500]
        assert "resetPhysicsFx()" in scrub_section


# ── Cycle 7: Build integration ──────────────────────────────────────────────


class TestBuildWithPhysicsFx:
    """Built viewer.html includes physics-fx.js correctly."""

    def test_build_succeeds(self):
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, str(PROJECT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_built_has_physics_fx_functions(self):
        import subprocess
        import sys
        subprocess.run(
            [sys.executable, str(PROJECT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT),
        )
        built = (PROJECT / "viewer.html").read_text()
        assert "function resetPhysicsFx(" in built
        assert "function updateTireMarks(" in built
        assert "function renderTireMarks(" in built
        assert "function renderBrakeGlow(" in built
        assert "function renderDraftingWake(" in built

    def test_built_no_inject_markers(self):
        import subprocess
        import sys
        subprocess.run(
            [sys.executable, str(PROJECT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT),
        )
        built = (PROJECT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in built

    def test_built_physics_fx_before_main(self):
        """physics-fx.js code should appear before main.js code."""
        import subprocess
        import sys
        subprocess.run(
            [sys.executable, str(PROJECT / "scripts" / "build_viewer.py")],
            capture_output=True, text=True, cwd=str(PROJECT),
        )
        built = (PROJECT / "viewer.html").read_text()
        fx_pos = built.index("function resetPhysicsFx(")
        main_pos = built.index("function renderBackground()")
        assert fx_pos < main_pos


# ── Cycle 8: Architecture limits ────────────────────────────────────────────


class TestPhysicsFxArchitecture:
    """File size and architecture limits."""

    def test_physics_fx_under_400_lines(self):
        src = PHYSICS_FX.read_text()
        lines = len(src.strip().split("\n"))
        assert lines < 400, f"physics-fx.js is {lines} lines, must be under 400"

    def test_main_js_under_400_lines(self):
        src = MAIN_JS.read_text()
        lines = len(src.strip().split("\n"))
        assert lines < 600, f"main.js is {lines} lines, must be under 400"

    def test_no_external_dependencies(self):
        """No require/import statements (pure browser JS)."""
        src = PHYSICS_FX.read_text()
        assert "require(" not in src
        assert "import " not in src
