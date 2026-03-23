"""Structural tests for the code terminal viewer component (T31.3 + T31.4)."""

import pathlib

VIEWER = pathlib.Path(__file__).resolve().parent.parent / "viewer"


class TestCodeTerminalFileExists:
    """T31.3: code-terminal.js exists with required functions."""

    def test_file_exists(self):
        assert (VIEWER / "js" / "code-terminal.js").is_file()

    def test_has_init_function(self):
        src = (VIEWER / "js" / "code-terminal.js").read_text()
        assert "function initCodeTerminal" in src

    def test_has_update_function(self):
        src = (VIEWER / "js" / "code-terminal.js").read_text()
        assert "function updateCodeTerminal" in src

    def test_has_render_grade_function(self):
        src = (VIEWER / "js" / "code-terminal.js").read_text()
        assert "function renderCodeGrade" in src

    def test_listens_for_car_selected(self):
        src = (VIEWER / "js" / "code-terminal.js").read_text()
        assert "car-selected" in src


class TestDashboardIntegration:
    """Dashboard HTML has the code terminal panel wired in."""

    def test_code_terminal_div_exists(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert 'id="codeTerminal"' in html

    def test_script_tag_included(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert 'src="js/code-terminal.js"' in html

    def test_script_before_main(self):
        html = (VIEWER / "dashboard.html").read_text()
        term_pos = html.index("code-terminal.js")
        main_pos = html.index("main.js")
        assert term_pos < main_pos

    def test_term_ok_css_class(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert ".term-ok" in html

    def test_term_glitch_css_class(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert ".term-glitch" in html

    def test_term_clamped_css_class(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert ".term-clamped" in html

    def test_term_badge_css_class(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert ".term-badge" in html

    def test_grade_card_css_class(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert ".grade-card" in html

    def test_grade_letter_css_class(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert ".grade-letter" in html

    def test_grade_fill_css_class(self):
        html = (VIEWER / "dashboard.html").read_text()
        assert ".grade-fill" in html


class TestMainJsWiring:
    """main.js calls initCodeTerminal and updateCodeTerminal."""

    def test_init_called_in_load_replay(self):
        src = (VIEWER / "js" / "main.js").read_text()
        assert "initCodeTerminal" in src

    def test_update_called_in_render(self):
        src = (VIEWER / "js" / "main.js").read_text()
        assert "updateCodeTerminal" in src
