"""Tests for car telemetry panel JS (T8.4)."""
import os

VIEWER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viewer"
)
JS_PATH = os.path.join(VIEWER_DIR, "js", "telemetry-panel.js")
HTML_PATH = os.path.join(VIEWER_DIR, "dashboard.html")


def _read_js():
    with open(JS_PATH) as f:
        return f.read()


def _read_html():
    with open(HTML_PATH) as f:
        return f.read()


# ── Structure tests ──────────────────────────────────────────────────────────


class TestTelemetryPanelStructure:
    """Telemetry panel JS file structure and exports."""

    def test_file_exists(self):
        assert os.path.isfile(JS_PATH)

    def test_not_stub(self):
        js = _read_js()
        assert len(js) > 100, "telemetry-panel.js should not be a stub"

    def test_line_count_under_250(self):
        js = _read_js()
        lines = js.strip().split("\n")
        assert len(lines) <= 250, f"telemetry-panel.js is {len(lines)} lines (max 250)"

    def test_defines_init_function(self):
        js = _read_js()
        assert "function initTelemetryPanel" in js

    def test_defines_update_function(self):
        js = _read_js()
        assert "function updateTelemetryPanel" in js

    def test_defines_helper_functions(self):
        js = _read_js()
        assert "function setText" in js
        assert "function setTextColor" in js
        assert "function setBar" in js

    def test_defines_sector_tracking(self):
        js = _read_js()
        assert "function updateSectorData" in js

    def test_defines_alert_system(self):
        js = _read_js()
        assert "function checkAlerts" in js
        assert "function pushAlert" in js

    def test_listens_for_car_selected(self):
        js = _read_js()
        assert "car-selected" in js


# ── DOM creation tests ───────────────────────────────────────────────────────


class TestTelemetryPanelDOM:
    """initTelemetryPanel creates correct DOM element IDs."""

    def test_creates_speed_readout(self):
        js = _read_js()
        assert "roSpeed" in js

    def test_creates_tire_readout(self):
        js = _read_js()
        assert "roTireVal" in js
        assert "roTireBar" in js
        assert "roCompound" in js
        assert "roTireAge" in js

    def test_creates_temp_readout(self):
        js = _read_js()
        assert "roTemp" in js
        assert "roTempStatus" in js

    def test_creates_fuel_readout(self):
        js = _read_js()
        assert "roFuelVal" in js
        assert "roFuelBar" in js

    def test_creates_drs_readout(self):
        js = _read_js()
        assert "roDRS" in js

    def test_creates_engine_readout(self):
        js = _read_js()
        assert "roEngine" in js

    def test_creates_dirty_air_readout(self):
        js = _read_js()
        assert "roDirtyVal" in js
        assert "roDirtyBar" in js

    def test_creates_gap_readouts(self):
        js = _read_js()
        assert "roGapAhead" in js
        assert "roGapBehind" in js

    def test_creates_pit_stops_readout(self):
        js = _read_js()
        assert "roPitStops" in js

    def test_creates_sector_elements(self):
        js = _read_js()
        for i in range(1, 4):
            assert f"secS{i}Time" in js, f"Missing sector S{i} time element"
            assert f"secS{i}Delta" in js, f"Missing sector S{i} delta element"
        assert "secLapTime" in js
        assert "secLapDelta" in js

    def test_ten_readout_rows(self):
        """All 10 readouts are present in the init HTML."""
        js = _read_js()
        readout_labels = [
            "Speed", "Tire", "Temp", "Fuel", "DRS",
            "Engine", "Dirty Air", "Gap", "Gap", "Pit Stops",
        ]
        for label in readout_labels:
            assert label in js, f"Missing readout label: {label}"


# ── Update logic tests ───────────────────────────────────────────────────────


class TestTelemetryPanelUpdate:
    """updateTelemetryPanel handles car data correctly."""

    def test_updates_speed(self):
        js = _read_js()
        assert "carData.speed" in js

    def test_updates_tire_wear_bar(self):
        js = _read_js()
        assert "tire_wear" in js

    def test_updates_compound_names(self):
        js = _read_js()
        assert "SOFT" in js
        assert "MED" in js
        assert "HARD" in js

    def test_tire_temp_optimal_window(self):
        js = _read_js()
        assert "OPTIMAL" in js
        assert "COLD" in js
        assert "HOT" in js

    def test_updates_fuel_pct(self):
        js = _read_js()
        assert "fuel_pct" in js

    def test_updates_drs_active(self):
        js = _read_js()
        assert "drs_active" in js
        assert "ACTIVE" in js

    def test_updates_engine_mode(self):
        js = _read_js()
        assert "engine_mode" in js

    def test_updates_dirty_air_factor(self):
        js = _read_js()
        assert "dirty_air_factor" in js

    def test_updates_gaps(self):
        js = _read_js()
        assert "gap_ahead_s" in js
        assert "gap_behind_s" in js

    def test_updates_pit_stops(self):
        js = _read_js()
        assert "pit_stops" in js

    def test_null_guard(self):
        """Function returns early if carData is null."""
        js = _read_js()
        assert "if (!carData) return" in js


# ── Sector tracking tests ────────────────────────────────────────────────────


class TestSectorTracking:
    """Sector data updates with color-coded deltas."""

    def test_tracks_personal_bests(self):
        js = _read_js()
        assert "_sectorBests" in js

    def test_tracks_session_bests(self):
        js = _read_js()
        assert "_sessionBestSectors" in js

    def test_purple_for_session_best(self):
        js = _read_js()
        assert "--accent-purple" in js

    def test_green_for_personal_best(self):
        js = _read_js()
        assert "--accent-green" in js

    def test_yellow_for_slower(self):
        js = _read_js()
        assert "--accent-yellow" in js

    def test_formats_sector_time(self):
        js = _read_js()
        assert ".toFixed(3)" in js


# ── Alert system tests ───────────────────────────────────────────────────────


class TestAlertSystem:
    """Alerts fire for key events."""

    def test_dirty_air_alert(self):
        js = _read_js()
        assert "DIRTY AIR" in js

    def test_tire_cliff_alert(self):
        js = _read_js()
        assert "TIRE CLIFF" in js

    def test_fuel_critical_alert(self):
        js = _read_js()
        assert "FUEL CRITICAL" in js

    def test_undercut_alert(self):
        js = _read_js()
        assert "UNDERCUT" in js

    def test_overcut_alert(self):
        js = _read_js()
        assert "OVERCUT" in js

    def test_max_three_alerts(self):
        js = _read_js()
        assert "children.length > 3" in js

    def test_auto_dismiss(self):
        js = _read_js()
        assert "setTimeout" in js
        assert "5000" in js

    def test_alert_types_used(self):
        """Alert types warning/danger/success are passed to pushAlert."""
        js = _read_js()
        assert "'warning'" in js
        assert "'danger'" in js
        assert "'success'" in js


# ── CSS tests ────────────────────────────────────────────────────────────────


class TestTelemetryCSS:
    """CSS styles added to dashboard.html for telemetry panel."""

    def test_readout_style(self):
        html = _read_html()
        assert ".readout" in html

    def test_ro_label_style(self):
        html = _read_html()
        assert ".ro-label" in html

    def test_ro_bar_style(self):
        html = _read_html()
        assert ".ro-bar" in html

    def test_bar_fill_style(self):
        html = _read_html()
        assert ".bar-fill" in html

    def test_sector_styles(self):
        html = _read_html()
        assert ".sector-header" in html
        assert ".sector-row" in html
        assert ".sector-time" in html
        assert ".sector-delta" in html

    def test_alert_styles(self):
        html = _read_html()
        assert ".alert-warning" in html
        assert ".alert-danger" in html
        assert ".alert-success" in html

    def test_alert_fade_animation(self):
        html = _read_html()
        assert "alertFade" in html


# ── Wiring tests ─────────────────────────────────────────────────────────────


class TestMainJSWiring:
    """main.js calls initTelemetryPanel and updateTelemetryPanel."""

    def _read_main(self):
        with open(os.path.join(VIEWER_DIR, "js", "main.js")) as f:
            return f.read()

    def test_calls_init_in_load_replay(self):
        js = self._read_main()
        assert "initTelemetryPanel" in js

    def test_calls_update_in_tick(self):
        js = self._read_main()
        assert "updateTelemetryPanel" in js
