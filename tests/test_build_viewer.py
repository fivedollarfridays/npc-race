"""Tests for scripts/build_viewer.py — viewer JS inliner build system."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestViewerShell:
    """viewer/viewer.html shell file exists and has correct structure."""

    def test_shell_exists(self):
        shell = PROJECT_ROOT / "viewer" / "viewer.html"
        assert shell.exists(), "viewer/viewer.html shell must exist"

    def test_shell_has_inject_marker(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "<!-- INJECT:js/main.js -->" in shell

    def test_shell_has_no_script_block(self):
        """Shell should not contain inline JS — it uses INJECT markers."""
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "<script>" not in shell

    def test_shell_has_doctype(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert shell.strip().startswith("<!DOCTYPE html>")

    def test_shell_has_styles(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "<style>" in shell

    def test_shell_has_html_body(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert '<div class="logo">' in shell


class TestMainJs:
    """viewer/js/main.js exists and contains expected code."""

    def test_main_js_exists(self):
        js = PROJECT_ROOT / "viewer" / "js" / "main.js"
        assert js.exists(), "viewer/js/main.js must exist"

    def test_main_js_has_toggle_play(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "function togglePlay()" in js

    def test_main_js_has_replay_state(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "let replay = null;" in js

    def test_main_js_has_render(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "function render()" in js


class TestBuildScript:
    """scripts/build_viewer.py produces correct output."""

    def test_build_runs_without_error(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_output_exists(self):
        out = PROJECT_ROOT / "viewer.html"
        assert out.exists(), "Built viewer.html must exist at project root"

    def test_output_has_script_tags(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<script>" in out, "Output must contain inlined <script> tags"

    def test_output_has_no_inject_markers(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in out, "Output must not contain INJECT markers"

    def test_output_starts_with_doctype(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert out.strip().startswith("<!DOCTYPE html>")

    def test_output_ends_with_html(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert out.strip().endswith("</html>")

    def test_output_has_npc_race(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "NPC" in out and "Race" in out

    def test_output_has_replay_json(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "replay.json" in out

    def test_output_has_toggle_play(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "togglePlay" in out

    def test_output_has_styles(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<style>" in out

    def test_output_preserves_size(self):
        """Built output should be similar size to original (not truncated)."""
        out = (PROJECT_ROOT / "viewer.html").read_text()
        # Original is 687 lines; built version should be close
        assert len(out) > 5000, "Output seems too small — may be truncated"
