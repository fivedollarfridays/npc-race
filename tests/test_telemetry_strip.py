"""Tests for telemetry strip JS — time-series charts (T8.5)."""
import os

VIEWER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "viewer"
)
JS_PATH = os.path.join(VIEWER_DIR, "js", "telemetry-strip.js")
MAIN_JS = os.path.join(VIEWER_DIR, "js", "main.js")


def _read_js() -> str:
    with open(JS_PATH) as f:
        return f.read()


def _read_main() -> str:
    with open(MAIN_JS) as f:
        return f.read()


# ── File structure ────────────────────────────────────────────────────────


class TestTelemetryStripExists:
    def test_file_exists(self) -> None:
        assert os.path.isfile(JS_PATH)

    def test_not_stub(self) -> None:
        js = _read_js()
        # Stub is ~3 lines; real implementation should be much longer
        assert len(js.strip().splitlines()) > 20, "telemetry-strip.js is still a stub"

    def test_line_count_under_limit(self) -> None:
        js = _read_js()
        lines = js.strip().splitlines()
        assert len(lines) <= 250, f"telemetry-strip.js is {len(lines)} LOC (max 250)"


# ── State and constants ───────────────────────────────────────────────────


class TestTelemetryStripState:
    def test_has_strip_history(self) -> None:
        js = _read_js()
        assert "_stripHistory" in js, "Missing _stripHistory state"

    def test_has_strip_window_constant(self) -> None:
        js = _read_js()
        assert "STRIP_WINDOW" in js, "Missing STRIP_WINDOW constant"
        assert "5000" in js, "STRIP_WINDOW should be 5000"

    def test_has_update_counter(self) -> None:
        js = _read_js()
        assert "_stripUpdateCounter" in js, "Missing _stripUpdateCounter"

    def test_has_strip_car(self) -> None:
        js = _read_js()
        assert "_stripCar" in js, "Missing _stripCar state"


# ── Public API functions ──────────────────────────────────────────────────


class TestTelemetryStripAPI:
    def test_has_init_function(self) -> None:
        js = _read_js()
        assert "function initTelemetryStrip" in js

    def test_has_update_function(self) -> None:
        js = _read_js()
        assert "function updateTelemetryStrip" in js

    def test_has_draw_speed_trace(self) -> None:
        js = _read_js()
        assert "drawSpeedTrace" in js

    def test_has_draw_tire_trace(self) -> None:
        js = _read_js()
        assert "drawTireTrace" in js

    def test_has_draw_gap_trace(self) -> None:
        js = _read_js()
        assert "drawGapTrace" in js

    def test_has_draw_line_utility(self) -> None:
        js = _read_js()
        assert "function drawLine" in js


# ── Data buffering ────────────────────────────────────────────────────────


class TestTelemetryStripBuffering:
    def test_buffers_speed(self) -> None:
        js = _read_js()
        assert "h.speed.push" in js, "Should buffer speed values"

    def test_buffers_tire_wear(self) -> None:
        js = _read_js()
        assert "h.tire_wear.push" in js, "Should buffer tire_wear values"

    def test_buffers_tire_temp(self) -> None:
        js = _read_js()
        assert "h.tire_temp.push" in js, "Should buffer tire_temp values"

    def test_buffers_gap(self) -> None:
        js = _read_js()
        assert "h.gap.push" in js, "Should buffer gap values"

    def test_trims_to_window(self) -> None:
        js = _read_js()
        assert "slice" in js, "Should trim data arrays with slice"

    def test_skip_frames_for_performance(self) -> None:
        js = _read_js()
        # Should only redraw every 3rd frame
        assert "% 3" in js, "Should skip frames (redraw every 3rd)"


# ── Chart rendering features ─────────────────────────────────────────────


class TestSpeedTraceFeatures:
    def test_dirty_air_shading(self) -> None:
        js = _read_js()
        assert "dirty" in js.lower(), "Speed trace should show dirty air zones"

    def test_sector_boundaries(self) -> None:
        js = _read_js()
        assert "sector" in js.lower(), "Speed trace should show sector boundaries"

    def test_speed_y_range(self) -> None:
        js = _read_js()
        # Speed trace should use 0-380 range
        assert "380" in js, "Speed trace yMax should be 380"

    def test_pit_zone_shading(self) -> None:
        js = _read_js()
        assert "pit" in js.lower(), "Speed trace should show pit zones"


class TestTireTraceFeatures:
    def test_dual_axis_wear_and_temp(self) -> None:
        js = _read_js()
        # Should draw both tire_wear and tire_temp lines
        assert "tire_wear" in js, "Tire trace should plot wear"
        assert "tire_temp" in js, "Tire trace should plot temp"

    def test_cliff_threshold_line(self) -> None:
        js = _read_js()
        # Cliff threshold around 0.78
        assert "0.78" in js or "cliff" in js.lower(), "Tire trace should show cliff threshold"


class TestGapTraceFeatures:
    def test_green_red_fill(self) -> None:
        js = _read_js()
        # Green for gaining, red for losing
        assert "34, 197, 94" in js, "Gap trace should use green for gaining"
        assert "239, 68, 68" in js, "Gap trace should use red for losing"

    def test_dynamic_y_max(self) -> None:
        js = _read_js()
        # Gap trace should compute dynamic yMax from data
        assert "Math.max" in js, "Gap trace should use dynamic yMax"


# ── Car selection ─────────────────────────────────────────────────────────


class TestCarSelection:
    def test_listens_for_car_selected_event(self) -> None:
        js = _read_js()
        assert "car-selected" in js, "Should listen for car-selected event"


# ── main.js wiring ───────────────────────────────────────────────────────


class TestMainJSWiring:
    def test_main_calls_init(self) -> None:
        main = _read_main()
        assert "initTelemetryStrip" in main, "main.js should call initTelemetryStrip"

    def test_main_calls_update(self) -> None:
        main = _read_main()
        assert "updateTelemetryStrip" in main, "main.js should call updateTelemetryStrip"
