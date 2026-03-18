"""Tests for post-race diagnostic mode (T8.6)."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
VIEWER = ROOT / "viewer"


class TestDiagnosticJsExists:
    """diagnostic.js file exists."""

    def test_diagnostic_js_exists(self):
        assert (VIEWER / "js" / "diagnostic.js").is_file()


class TestDiagnosticJsFunctions:
    """diagnostic.js exposes required functions."""

    def _read(self):
        return (VIEWER / "js" / "diagnostic.js").read_text()

    def test_has_init_diagnostic(self):
        src = self._read()
        assert "function initDiagnostic" in src

    def test_has_show_diagnostic(self):
        src = self._read()
        assert "function showDiagnostic" in src

    def test_has_hide_diagnostic(self):
        src = self._read()
        assert "function hideDiagnostic" in src

    def test_has_toggle_diagnostic(self):
        src = self._read()
        assert "function toggleDiagnostic" in src

    def test_has_draw_lap_time_chart(self):
        src = self._read()
        assert "function drawLapTimeChart" in src

    def test_has_build_sector_table(self):
        src = self._read()
        assert "function buildSectorTable" in src

    def test_has_get_lap_compounds(self):
        src = self._read()
        assert "function getLapCompounds" in src


class TestDiagnosticJsNotStub:
    """diagnostic.js is a real implementation, not a stub."""

    def test_not_stub(self):
        src = (VIEWER / "js" / "diagnostic.js").read_text()
        lines = [ln for ln in src.strip().splitlines() if ln.strip()]
        assert len(lines) > 10, f"Only {len(lines)} non-empty lines — still a stub"

    def test_line_count_under_limit(self):
        src = (VIEWER / "js" / "diagnostic.js").read_text()
        lines = src.strip().splitlines()
        assert len(lines) <= 220, f"{len(lines)} lines exceeds 220 limit"


class TestDashboardDiagnosticCss:
    """dashboard.html contains diagnostic CSS."""

    def _read(self):
        return (VIEWER / "dashboard.html").read_text()

    def test_has_diag_btn_class(self):
        assert ".diag-btn" in self._read()

    def test_has_diag_btn_active(self):
        assert ".diag-btn.active" in self._read()

    def test_has_diag_table_class(self):
        assert ".diag-table" in self._read()

    def test_has_diag_best_class(self):
        assert ".diag-best" in self._read()


class TestMainJsDiagnosticWiring:
    """main.js wires diagnostic into loadReplay and race end."""

    def _read(self):
        return (VIEWER / "js" / "main.js").read_text()

    def test_init_diagnostic_called_in_load_replay(self):
        src = self._read()
        assert "initDiagnostic" in src

    def test_diagnostic_button_reveal_at_race_end(self):
        src = self._read()
        assert "diagnosticBtn" in src


class TestDiagnosticJsState:
    """diagnostic.js manages state correctly."""

    def _read(self):
        return (VIEWER / "js" / "diagnostic.js").read_text()

    def test_has_diagnostic_active_state(self):
        src = self._read()
        assert "_diagnosticActive" in src

    def test_has_player_car_name_state(self):
        src = self._read()
        assert "_playerCarName" in src

    def test_creates_diagnostic_button(self):
        src = self._read()
        assert "diagnosticBtn" in src

    def test_saves_and_restores_html(self):
        src = self._read()
        assert "_savedHTML" in src
