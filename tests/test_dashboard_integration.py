"""Sprint 8 integration gate -- pit wall dashboard verification.

Verifies all dashboard panels have correct JS implementations,
dashboard.html loads all modules, and replay data has all fields
needed by the dashboard.
"""

import json
import os

import pytest

pytestmark = pytest.mark.slow

VIEWER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viewer"
)
JS_DIR = os.path.join(VIEWER_DIR, "js")
CARS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars"
)


def _run_race(tmp_path, **kw):
    from engine import run_race

    out = str(tmp_path / "replay.json")
    kw["output"] = out
    kw.setdefault("car_dir", CARS_DIR)
    run_race(**kw)
    with open(out) as f:
        return json.load(f)


class TestDashboardJsModules:
    """All 4 dashboard JS modules are real implementations (not stubs)."""

    def test_timing_tower_not_stub(self):
        js = open(os.path.join(JS_DIR, "timing-tower.js")).read()
        assert len(js.splitlines()) > 50, "timing-tower.js is still a stub"
        assert "updateTimingTower" in js

    def test_telemetry_panel_not_stub(self):
        js = open(os.path.join(JS_DIR, "telemetry-panel.js")).read()
        assert len(js.splitlines()) > 50, "telemetry-panel.js is still a stub"
        assert "updateTelemetryPanel" in js

    def test_telemetry_strip_not_stub(self):
        js = open(os.path.join(JS_DIR, "telemetry-strip.js")).read()
        assert len(js.splitlines()) > 50, "telemetry-strip.js is still a stub"
        assert "updateTelemetryStrip" in js

    def test_diagnostic_not_stub(self):
        js = open(os.path.join(JS_DIR, "diagnostic.js")).read()
        assert len(js.splitlines()) > 50, "diagnostic.js is still a stub"
        assert "showDiagnostic" in js


class TestDashboardHtmlComplete:
    """dashboard.html has all required elements."""

    def test_has_all_panel_ids(self):
        html = open(os.path.join(VIEWER_DIR, "dashboard.html")).read()
        for pid in [
            "statusBar",
            "timingTower",
            "trackView",
            "carTelemetry",
            "telemetryStrip",
            "controls",
        ]:
            assert f'id="{pid}"' in html, f"Missing {pid}"

    def test_has_all_js_scripts(self):
        html = open(os.path.join(VIEWER_DIR, "dashboard.html")).read()
        required = [
            "data-enrichment.js",
            "track-renderer.js",
            "car-renderer.js",
            "overlay.js",
            "sound-engine.js",
            "physics-fx.js",
            "camera.js",
            "timing-tower.js",
            "telemetry-panel.js",
            "telemetry-strip.js",
            "diagnostic.js",
            "main.js",
        ]
        for js in required:
            assert js in html, f"Missing script: {js}"

    def test_has_css_variables(self):
        html = open(os.path.join(VIEWER_DIR, "dashboard.html")).read()
        for var in [
            "--bg-primary",
            "--accent-purple",
            "--accent-green",
            "--accent-yellow",
            "--font-mono",
        ]:
            assert var in html, f"Missing CSS variable: {var}"

    def test_has_3_telemetry_canvases(self):
        html = open(os.path.join(VIEWER_DIR, "dashboard.html")).read()
        for cid in ["speedTrace", "tireTrace", "gapTrace"]:
            assert f'id="{cid}"' in html, f"Missing canvas: {cid}"


class TestReplayHasDashboardFields:
    """Replay frames contain all fields needed by dashboard panels."""

    def test_all_dashboard_fields_present(self, tmp_path):
        replay = _run_race(tmp_path, track_name="monza", laps=2)
        required = [
            "speed",
            "tire_wear",
            "tire_temp",
            "tire_compound",
            "fuel_pct",
            "engine_mode",
            "drs_active",
            "in_dirty_air",
            "dirty_air_factor",
            "gap_ahead_s",
            "gap_behind_s",
            "current_sector",
            "elapsed_s",
            "tire_age_laps",
            "pit_stops",
            "position",
            "lap",
            "name",
            "color",
        ]
        frame = replay["frames"][500]
        for car in frame:
            for field in required:
                assert field in car, f"Missing field '{field}' for {car['name']}"

    def test_results_have_timing_data(self, tmp_path):
        replay = _run_race(tmp_path, track_name="monza", laps=2)
        for r in replay["results"]:
            assert "total_time_s" in r
            assert "best_lap_s" in r
            assert "lap_times" in r
            assert "pit_stops" in r


class TestMainJsWiring:
    """main.js calls all dashboard init and update functions."""

    def test_main_calls_init_functions(self):
        js = open(os.path.join(JS_DIR, "main.js")).read()
        assert "initTimingTower" in js
        assert "initTelemetryPanel" in js
        assert "initTelemetryStrip" in js
        assert "initDiagnostic" in js

    def test_main_calls_update_functions(self):
        js = open(os.path.join(JS_DIR, "main.js")).read()
        assert "updateTimingTower" in js
        assert "updateTelemetryPanel" in js
        assert "updateTelemetryStrip" in js

    def test_main_has_status_bar_update(self):
        js = open(os.path.join(JS_DIR, "main.js")).read()
        assert "updateStatusBar" in js
        assert "formatTime" in js


class TestPlayPyServesDashboard:
    """play.py serves dashboard.html by default."""

    def test_references_dashboard(self):
        with open("play.py") as f:
            assert "dashboard.html" in f.read()


class TestArchCompliance:
    """File size limits respected."""

    def test_simulation_under_limit(self):
        with open("engine/simulation.py") as f:
            assert len(f.readlines()) <= 395, "simulation.py over 395 lines"

    def test_dashboard_js_module_sizes(self):
        limits = {
            "timing-tower.js": 200,
            "telemetry-panel.js": 280,
            "telemetry-strip.js": 280,
            "diagnostic.js": 250,
        }
        for name, limit in limits.items():
            with open(os.path.join(JS_DIR, name)) as f:
                lines = len(f.readlines())
            assert lines <= limit, f"{name} has {lines} lines (limit {limit})"
