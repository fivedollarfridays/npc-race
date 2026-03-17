"""Tests for T2.7: Sound engine integration with viewer HTML and main.js."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestViewerHtmlSoundIntegration:
    """viewer.html has sound engine INJECT marker and volume controls."""

    def test_has_sound_engine_inject(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "<!-- INJECT:js/sound-engine.js -->" in shell

    def test_sound_engine_before_main(self):
        """sound-engine.js must be injected before main.js."""
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        sound_pos = shell.index("INJECT:js/sound-engine.js")
        main_pos = shell.index("INJECT:js/main.js")
        assert sound_pos < main_pos

    def test_has_mute_button(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert 'id="muteBtn"' in shell

    def test_has_volume_slider(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert 'id="volumeSlider"' in shell

    def test_mute_button_calls_toggle_mute(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "toggleMute()" in shell

    def test_volume_slider_calls_set_volume(self):
        shell = (PROJECT_ROOT / "viewer" / "viewer.html").read_text()
        assert "setVolume(" in shell


class TestMainJsSoundHooks:
    """main.js calls sound engine functions at correct points."""

    def test_toggle_play_calls_init_audio(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "initAudio()" in js

    def test_tick_calls_update_sound(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "updateSound(" in js

    def test_pause_calls_pause_sound(self):
        """When pausing, should call pauseSound()."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        assert "pauseSound()" in js

    def test_scrubber_calls_pause_sound(self):
        """When scrubbing, should call pauseSound()."""
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        scrub_idx = js.index("scrubber")
        scrub_section = js[scrub_idx:]
        assert "pauseSound()" in scrub_section


class TestBuildWithSoundEngine:
    """Built viewer.html includes sound engine correctly."""

    def test_build_succeeds(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "build_viewer.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_built_has_init_audio(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "function initAudio()" in out

    def test_built_has_update_sound(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "function updateSound(" in out

    def test_built_has_no_inject_markers(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert "<!-- INJECT:" not in out

    def test_built_has_three_script_tags(self):
        """Should have at least 3 inlined script blocks (enrichment, sound, main)."""
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert out.count("<script>") >= 3

    def test_built_sound_before_main(self):
        """initAudio should appear before togglePlay in built output."""
        out = (PROJECT_ROOT / "viewer.html").read_text()
        sound_pos = out.index("function initAudio()")
        main_pos = out.index("function togglePlay()")
        assert sound_pos < main_pos

    def test_built_has_volume_controls(self):
        out = (PROJECT_ROOT / "viewer.html").read_text()
        assert 'id="muteBtn"' in out
        assert 'id="volumeSlider"' in out


class TestSoundEngineFileSize:
    """Sound engine JS file stays within limits."""

    def test_under_400_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        lines = js.strip().split("\n")
        assert len(lines) < 400, f"sound-engine.js is {len(lines)} lines, must be < 400"

    def test_main_js_under_400_lines(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "main.js").read_text()
        lines = js.strip().split("\n")
        assert len(lines) < 400, f"main.js is {len(lines)} lines, must be < 400"
