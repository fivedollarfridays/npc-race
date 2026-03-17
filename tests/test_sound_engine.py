"""Tests for T2.7: Sound engine JS module structure and audio nodes."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestSoundEngineFileExists:
    """viewer/js/sound-engine.js exists and has core structure."""

    def test_file_exists(self):
        js = PROJECT_ROOT / "viewer" / "js" / "sound-engine.js"
        assert js.exists(), "viewer/js/sound-engine.js must exist"

    def test_has_sound_object(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "const sound =" in js

    def test_sound_has_ctx(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "ctx:" in js

    def test_sound_has_master_gain(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "master:" in js

    def test_has_init_audio(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function initAudio()" in js

    def test_init_audio_creates_audio_context(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "AudioContext" in js

    def test_init_audio_gates_on_initialized(self):
        """Should not re-initialize if already initialized."""
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "sound.initialized" in js

    def test_has_create_noise_buffer(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function createNoiseBuffer(" in js

    def test_has_create_brown_noise_buffer(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function createBrownNoiseBuffer(" in js

    def test_no_external_audio_files(self):
        """Must not reference any audio file URLs."""
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert ".mp3" not in js
        assert ".wav" not in js
        assert ".ogg" not in js


class TestSoundEngineNodes:
    """Sound engine creates correct Web Audio nodes."""

    def test_has_sawtooth_engine(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "'sawtooth'" in js

    def test_has_engine_gain(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "engineGain:" in js

    def test_has_second_harmonic(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "engine2:" in js

    def test_has_aero_whoosh(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "aero:" in js
        assert "aeroGain:" in js

    def test_has_tire_squeal(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "tireNode:" in js or "tire:" in js
        assert "tireGain:" in js

    def test_tire_uses_bandpass(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "'bandpass'" in js

    def test_has_crowd_ambience(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "crowd:" in js
        assert "crowdGain:" in js

    def test_muted_default_false(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "muted: false" in js


class TestSoundUpdateFunction:
    """updateSound maps leader car data to audio parameters."""

    def test_has_update_sound(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function updateSound(" in js

    def test_engine_pitch_scales_with_speed(self):
        """Engine frequency should scale with leader speed."""
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "leader.speed" in js or "speed" in js
        assert "frequency" in js

    def test_uses_set_target_at_time(self):
        """Should use setTargetAtTime for smooth transitions."""
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "setTargetAtTime" in js

    def test_aero_scales_with_speed(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "aeroGain" in js or "aero" in js

    def test_tire_squeal_uses_curvature(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "curv" in js

    def test_has_downshift_pop(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function triggerDownshiftPop()" in js

    def test_has_crowd_swell(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function triggerCrowdSwell()" in js


class TestSoundControls:
    """Sound engine control functions: pause, volume, mute."""

    def test_has_pause_sound(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function pauseSound()" in js

    def test_pause_fades_out(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        pause_idx = js.index("function pauseSound()")
        next_fn = js.find("\nfunction ", pause_idx + 1)
        pause_body = js[pause_idx:next_fn] if next_fn > 0 else js[pause_idx:]
        assert "setTargetAtTime(0" in pause_body

    def test_has_set_volume(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function setVolume(" in js

    def test_has_toggle_mute(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "function toggleMute()" in js

    def test_toggle_mute_flips_state(self):
        js = (PROJECT_ROOT / "viewer" / "js" / "sound-engine.js").read_text()
        assert "sound.muted = !sound.muted" in js
