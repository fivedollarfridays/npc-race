"""Tests for timing tower JS implementation (T8.3)."""
import os

VIEWER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viewer"
)
JS_PATH = os.path.join(VIEWER_DIR, "js", "timing-tower.js")
HTML_PATH = os.path.join(VIEWER_DIR, "dashboard.html")
MAIN_JS_PATH = os.path.join(VIEWER_DIR, "js", "main.js")


def _read_js():
    with open(JS_PATH) as f:
        return f.read()


def _read_html():
    with open(HTML_PATH) as f:
        return f.read()


def _read_main():
    with open(MAIN_JS_PATH) as f:
        return f.read()


# ── State variables ──────────────────────────────────────────────────────────


class TestTimingTowerState:
    def test_has_selected_car_state(self):
        js = _read_js()
        assert "_selectedCar" in js, "Missing _selectedCar state variable"

    def test_has_prev_gaps_state(self):
        js = _read_js()
        assert "_prevGaps" in js, "Missing _prevGaps state variable"


# ── initTimingTower ──────────────────────────────────────────────────────────


class TestInitTimingTower:
    def test_function_exists(self):
        js = _read_js()
        assert "function initTimingTower" in js

    def test_creates_tower_rows(self):
        js = _read_js()
        assert "towerRows" in js, "Should reference towerRows container"

    def test_creates_row_elements(self):
        js = _read_js()
        assert "tower-row" in js, "Should create tower-row elements"

    def test_has_position_span(self):
        js = _read_js()
        assert "tower-pos" in js, "Should have position span"

    def test_has_color_span(self):
        js = _read_js()
        assert "tower-color" in js, "Should have color indicator span"

    def test_has_name_span(self):
        js = _read_js()
        assert "tower-name" in js, "Should have name span"

    def test_has_gap_span(self):
        js = _read_js()
        assert "tower-gap" in js, "Should have gap span"

    def test_has_compound_indicator(self):
        js = _read_js()
        assert "tower-compound" in js, "Should have compound indicator"

    def test_has_tire_age(self):
        js = _read_js()
        assert "tower-tire-age" in js, "Should have tire age span"

    def test_has_wear_bar(self):
        js = _read_js()
        assert "tower-wear-bar" in js, "Should have wear bar"
        assert "wear-fill" in js, "Should have wear fill element"

    def test_adds_click_listener(self):
        js = _read_js()
        assert "click" in js, "Should add click event listener"
        assert "selectCar" in js, "Click should call selectCar"

    def test_selects_first_car_by_default(self):
        js = _read_js()
        # Should select first car after creating rows
        assert "cars[0]" in js or "cars.length" in js


# ── updateTimingTower ────────────────────────────────────────────────────────


class TestUpdateTimingTower:
    def test_function_exists(self):
        js = _read_js()
        assert "function updateTimingTower" in js

    def test_sorts_by_position(self):
        js = _read_js()
        assert "position" in js, "Should sort cars by position"

    def test_shows_leader_label(self):
        js = _read_js()
        assert "LEADER" in js, "Leader should show LEADER text"

    def test_shows_gap_seconds(self):
        js = _read_js()
        assert "gap_ahead_s" in js, "Should reference gap_ahead_s"

    def test_has_gaining_losing_classes(self):
        js = _read_js()
        assert "gaining" in js, "Should have gaining CSS class"
        assert "losing" in js, "Should have losing CSS class"

    def test_has_compound_classes(self):
        js = _read_js()
        assert "compound-" in js, "Should have compound CSS classes"

    def test_has_tire_age_display(self):
        js = _read_js()
        assert "tire_age_laps" in js, "Should reference tire_age_laps"

    def test_has_wear_bar_update(self):
        js = _read_js()
        assert "tire_wear" in js, "Should reference tire_wear"
        assert "wear-critical" in js, "Should have critical wear class"
        assert "wear-warning" in js, "Should have warning wear class"

    def test_has_fastest_lap_marker(self):
        js = _read_js()
        assert "fastest-lap" in js, "Should mark fastest lap"
        assert "best_lap_s" in js, "Should reference best_lap_s"

    def test_has_selected_highlight(self):
        js = _read_js()
        assert "selected" in js, "Should toggle selected class"

    def test_has_pit_status(self):
        js = _read_js()
        assert "in-pit" in js, "Should toggle in-pit class"
        assert "pit_status" in js, "Should reference pit_status"

    def test_has_finished_state(self):
        js = _read_js()
        assert "finished" in js, "Should handle finished cars"
        assert "FIN" in js, "Finished cars should show FIN"

    def test_reorders_by_position(self):
        js = _read_js()
        assert "order" in js, "Should set CSS order for position"

    def test_updates_fastest_lap_footer(self):
        js = _read_js()
        assert "fastestLapInfo" in js, "Should update fastest lap footer"


# ── selectCar ────────────────────────────────────────────────────────────────


class TestSelectCar:
    def test_function_exists(self):
        js = _read_js()
        assert "function selectCar" in js

    def test_dispatches_custom_event(self):
        js = _read_js()
        assert "car-selected" in js, "Should dispatch car-selected event"
        assert "CustomEvent" in js, "Should use CustomEvent"

    def test_toggles_selected_class(self):
        js = _read_js()
        assert "selected" in js, "Should toggle selected class on rows"


# ── CSS in dashboard.html ────────────────────────────────────────────────────


class TestTimingTowerCSS:
    def test_tower_row_style(self):
        html = _read_html()
        assert ".tower-row" in html, "Missing .tower-row CSS"

    def test_tower_row_selected_style(self):
        html = _read_html()
        assert ".tower-row.selected" in html, "Missing selected row CSS"

    def test_tower_pos_style(self):
        html = _read_html()
        assert ".tower-pos" in html, "Missing .tower-pos CSS"

    def test_fastest_lap_style(self):
        html = _read_html()
        assert ".fastest-lap" in html, "Missing fastest-lap CSS"

    def test_compound_styles(self):
        html = _read_html()
        assert ".compound-soft" in html, "Missing soft compound CSS"
        assert ".compound-medium" in html, "Missing medium compound CSS"
        assert ".compound-hard" in html, "Missing hard compound CSS"

    def test_wear_bar_styles(self):
        html = _read_html()
        assert ".tower-wear-bar" in html, "Missing wear bar CSS"
        assert ".wear-fill" in html, "Missing wear fill CSS"
        assert ".wear-fill.wear-warning" in html, "Missing wear warning CSS"
        assert ".wear-fill.wear-critical" in html, "Missing wear critical CSS"

    def test_gaining_losing_styles(self):
        html = _read_html()
        assert ".tower-gap.gaining" in html, "Missing gaining gap CSS"
        assert ".tower-gap.losing" in html, "Missing losing gap CSS"

    def test_in_pit_style(self):
        html = _read_html()
        assert ".tower-row.in-pit" in html, "Missing in-pit CSS"

    def test_finished_style(self):
        html = _read_html()
        assert ".tower-row.finished" in html, "Missing finished CSS"


# ── main.js wiring ───────────────────────────────────────────────────────────


class TestMainJsWiring:
    def test_calls_init_timing_tower(self):
        main = _read_main()
        assert "initTimingTower" in main, "main.js should call initTimingTower"

    def test_calls_update_timing_tower(self):
        main = _read_main()
        assert "updateTimingTower" in main, "main.js should call updateTimingTower"

    def test_has_format_time(self):
        main = _read_main()
        assert "formatTime" in main, "main.js should have formatTime function"

    def test_updates_lap_counter(self):
        main = _read_main()
        assert "lapCounter" in main, "main.js should update lap counter"

    def test_updates_race_clock(self):
        main = _read_main()
        assert "raceClock" in main, "main.js should update race clock"


# ── File size ────────────────────────────────────────────────────────────────


class TestTimingTowerFileSize:
    def test_not_a_stub(self):
        js = _read_js()
        line_count = len(js.strip().splitlines())
        assert line_count > 20, f"timing-tower.js is still a stub ({line_count} lines)"

    def test_under_180_lines(self):
        js = _read_js()
        line_count = len(js.strip().splitlines())
        assert line_count <= 180, f"timing-tower.js too long ({line_count} lines)"
