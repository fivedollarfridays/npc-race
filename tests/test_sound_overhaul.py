"""Sprint 14 integration gate — sound overhaul verification (T14.5)."""

import pathlib


SOUND_JS = pathlib.Path("viewer/js/sound-engine.js").read_text()
MAIN_JS = pathlib.Path("viewer/js/main.js").read_text()


class TestSpatialAudio:
    def test_sound_engine_has_spatial_functions(self):
        assert "initSpatialAudio" in SOUND_JS
        assert "updateSpatialAudio" in SOUND_JS

    def test_sound_engine_has_car_slots(self):
        assert "_carAudioSlots" in SOUND_JS


class TestTurboWhistle:
    def test_turbo_whistle_exists(self):
        assert "triggerTurboWhistle" in SOUND_JS

    def test_turbo_oscillator_created(self):
        assert "_turboOsc" in SOUND_JS
        assert "_turboGain" in SOUND_JS


class TestDramaCrowd:
    def test_drama_score_in_sound_engine(self):
        assert "updateDramaScore" in SOUND_JS
        assert "_dramaScore" in SOUND_JS

    def test_crowd_swell_magnitude(self):
        # triggerCrowdSwell accepts magnitude parameter
        assert "triggerCrowdSwell(magnitude)" in SOUND_JS or "triggerCrowdSwell(mag" in SOUND_JS

    def test_events_wired_in_main(self):
        assert "_eventsByTick" in MAIN_JS
        assert "updateDramaScore" in MAIN_JS


class TestCameraMix:
    def test_camera_mix_in_sound_engine(self):
        assert "setCameraMix" in SOUND_JS

    def test_mix_profiles(self):
        assert "_mixProfiles" in SOUND_JS
        assert "onboard" in SOUND_JS
        assert "follow" in SOUND_JS

    def test_camera_mix_wired_in_main(self):
        assert "setCameraMix" in MAIN_JS


class TestArchCompliance:
    def test_sound_engine_under_limits(self):
        lines = len(SOUND_JS.splitlines())
        assert lines <= 350, f"sound-engine.js has {lines} lines"

    def test_simulation_unchanged(self):
        sim = pathlib.Path("engine/simulation.py").read_text()
        assert len(sim.splitlines()) <= 400
        assert sim.count("\n    def ") + sim.count("\ndef ") <= 15
