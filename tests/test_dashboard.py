"""Tests for pit wall dashboard layout."""
import os

VIEWER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viewer"
)


def test_dashboard_html_exists():
    assert os.path.isfile(os.path.join(VIEWER_DIR, "dashboard.html"))


def test_dashboard_has_panel_ids():
    with open(os.path.join(VIEWER_DIR, "dashboard.html")) as f:
        html = f.read()
    for panel_id in [
        "statusBar",
        "timingTower",
        "trackView",
        "carTelemetry",
        "telemetryStrip",
        "controls",
    ]:
        assert f'id="{panel_id}"' in html, f"Missing panel id: {panel_id}"


def test_dashboard_has_canvas_ids():
    with open(os.path.join(VIEWER_DIR, "dashboard.html")) as f:
        html = f.read()
    for canvas_id in ["trackBg", "carLayer", "overlayLayer"]:
        assert f'id="{canvas_id}"' in html, f"Missing canvas id: {canvas_id}"


def test_dashboard_has_telemetry_canvases():
    with open(os.path.join(VIEWER_DIR, "dashboard.html")) as f:
        html = f.read()
    for canvas_id in ["speedTrace", "tireTrace", "gapTrace"]:
        assert f'id="{canvas_id}"' in html, f"Missing telemetry canvas: {canvas_id}"


def test_dashboard_has_new_js_modules():
    with open(os.path.join(VIEWER_DIR, "dashboard.html")) as f:
        html = f.read()
    for js in [
        "timing-tower.js",
        "telemetry-panel.js",
        "telemetry-strip.js",
        "diagnostic.js",
    ]:
        assert js in html, f"Missing JS module: {js}"


def test_dashboard_has_existing_js():
    with open(os.path.join(VIEWER_DIR, "dashboard.html")) as f:
        html = f.read()
    for js in [
        "main.js",
        "data-enrichment.js",
        "track-renderer.js",
        "car-renderer.js",
    ]:
        assert js in html, f"Missing existing JS: {js}"


def test_dashboard_has_css_grid():
    with open(os.path.join(VIEWER_DIR, "dashboard.html")) as f:
        html = f.read()
    assert "grid-template-rows" in html, "Missing CSS grid rows"
    assert "grid-template-columns" in html, "Missing CSS grid columns"


def test_dashboard_has_dark_theme():
    with open(os.path.join(VIEWER_DIR, "dashboard.html")) as f:
        html = f.read()
    assert "#0d1117" in html, "Missing dark theme bg-primary"
    assert "JetBrains Mono" in html, "Missing monospace font"


def test_stub_js_files_exist():
    for js in [
        "timing-tower.js",
        "telemetry-panel.js",
        "telemetry-strip.js",
        "diagnostic.js",
    ]:
        path = os.path.join(VIEWER_DIR, "js", js)
        assert os.path.isfile(path), f"Missing stub JS file: {js}"


def test_play_py_references_dashboard():
    play_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "play.py"
    )
    with open(play_path) as f:
        content = f.read()
    assert "dashboard.html" in content, "play.py should reference dashboard.html"
