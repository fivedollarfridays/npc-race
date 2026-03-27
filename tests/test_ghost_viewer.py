"""Tests for ghost rendering in viewer (T46.5)."""

import pathlib

VIEWER_DIR = pathlib.Path(__file__).resolve().parent.parent / "viewer"
MAIN_JS = VIEWER_DIR / "js" / "main.js"
CAR_RENDERER_JS = VIEWER_DIR / "js" / "car-renderer.js"
EFF_PANEL_JS = VIEWER_DIR / "js" / "efficiency-panel.js"
DASHBOARD_HTML = VIEWER_DIR / "dashboard.html"


# ── Cycle 1: Ghost detection + translucent rendering ──────────────────────


def test_main_js_has_ghost_detection():
    """main.js or car-renderer.js contains isGhostCar function."""
    main_src = MAIN_JS.read_text()
    car_src = CAR_RENDERER_JS.read_text()
    combined = main_src + car_src
    assert "isGhostCar" in combined, "Missing isGhostCar function"


def test_car_renderer_sets_alpha_for_ghost():
    """car-renderer.js sets globalAlpha for ghost cars."""
    src = CAR_RENDERER_JS.read_text()
    assert "globalAlpha" in src, "Missing globalAlpha for ghost transparency"


def test_car_renderer_resets_alpha():
    """car-renderer.js resets globalAlpha to 1.0 after ghost rendering."""
    src = CAR_RENDERER_JS.read_text()
    assert "globalAlpha = 1" in src or "globalAlpha=1" in src, (
        "Missing globalAlpha reset after ghost rendering"
    )


# ── Cycle 2: Ghost column in efficiency panel ────────────────────────────


def test_efficiency_panel_has_ghost_column():
    """efficiency-panel.js contains eff-ghost elements."""
    src = EFF_PANEL_JS.read_text()
    assert "eff-ghost" in src, "Missing ghost column in efficiency panel"


def test_efficiency_panel_update_accepts_all_cars():
    """updateEfficiencyPanel accepts allCars parameter for ghost comparison."""
    src = EFF_PANEL_JS.read_text()
    assert "allCars" in src, "updateEfficiencyPanel missing allCars param"


def test_main_js_passes_all_cars_to_efficiency():
    """main.js passes allCars to updateEfficiencyPanel."""
    src = MAIN_JS.read_text()
    # Should call updateEfficiencyPanel with both carData and allCars
    assert "updateEfficiencyPanel(selectedData," in src or \
           "updateEfficiencyPanel(selectedData, " in src, (
        "main.js should pass allCars to updateEfficiencyPanel"
    )


def test_efficiency_panel_ghost_color_coding():
    """Ghost values are color-coded: red if worse, green if better."""
    src = EFF_PANEL_JS.read_text()
    assert "ghostLabel.style.color" in src, "Missing ghost color-coding logic"


# ── Cycle 3: Ghost delta display ─────────────────────────────────────────


def test_efficiency_panel_has_ghost_delta():
    """efficiency-panel.js creates ghost-delta element for gap display."""
    src = EFF_PANEL_JS.read_text()
    assert "ghost-delta" in src, "Missing ghost-delta element in efficiency panel"


def test_efficiency_panel_has_ghost_header_labels():
    """Efficiency panel shows 'You' and 'Ghost' header labels."""
    src = EFF_PANEL_JS.read_text()
    assert "You" in src, "Missing 'You' header label"
    assert "Ghost" in src, "Missing 'Ghost' header label"
