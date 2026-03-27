"""Tests for T46.4 — Live efficiency HUD in viewer dashboard."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWER = ROOT / "viewer"


def test_efficiency_panel_js_exists():
    """efficiency-panel.js must exist in viewer/js/."""
    path = VIEWER / "js" / "efficiency-panel.js"
    assert path.exists(), f"Missing {path}"


def test_efficiency_panel_has_init_function():
    """efficiency-panel.js must define initEfficiencyPanel."""
    text = (VIEWER / "js" / "efficiency-panel.js").read_text()
    assert "function initEfficiencyPanel" in text


def test_efficiency_panel_has_update_function():
    """efficiency-panel.js must define updateEfficiencyPanel."""
    text = (VIEWER / "js" / "efficiency-panel.js").read_text()
    assert "function updateEfficiencyPanel" in text


def test_efficiency_panel_maps_all_three_fields():
    """Panel must reference gearbox_efficiency, cooling_efficiency, efficiency_product."""
    text = (VIEWER / "js" / "efficiency-panel.js").read_text()
    for field in ("gearbox_efficiency", "cooling_efficiency", "efficiency_product"):
        assert field in text, f"Missing field mapping: {field}"


def test_efficiency_panel_color_thresholds():
    """Panel must have green/yellow/red color thresholds."""
    text = (VIEWER / "js" / "efficiency-panel.js").read_text()
    assert "#22c55e" in text, "Missing green color"
    assert "#eab308" in text, "Missing yellow color"
    assert "#ef4444" in text, "Missing red color"


def test_dashboard_has_efficiency_div():
    """dashboard.html must contain an efficiency-panel div."""
    html = (VIEWER / "dashboard.html").read_text()
    assert 'id="efficiency-panel"' in html


def test_dashboard_has_efficiency_css():
    """dashboard.html must contain CSS for #efficiency-panel."""
    html = (VIEWER / "dashboard.html").read_text()
    assert "#efficiency-panel" in html
    assert ".eff-bar-fill" in html


def test_dashboard_loads_efficiency_script():
    """dashboard.html must load efficiency-panel.js via script tag."""
    html = (VIEWER / "dashboard.html").read_text()
    assert 'src="js/efficiency-panel.js"' in html


def test_main_js_calls_init_efficiency():
    """main.js must call initEfficiencyPanel during load."""
    text = (VIEWER / "js" / "main.js").read_text()
    assert "initEfficiencyPanel" in text


def test_main_js_calls_update_efficiency():
    """main.js must call updateEfficiencyPanel during frame update."""
    text = (VIEWER / "js" / "main.js").read_text()
    assert "updateEfficiencyPanel" in text
