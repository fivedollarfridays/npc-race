"""Sprint 15 integration gate — viewer polish verification (T15.5)."""

import pathlib

CAMERA_JS = pathlib.Path("viewer/js/camera.js").read_text()
CAR_RENDERER_JS = pathlib.Path("viewer/js/car-renderer.js").read_text()
TRACK_RENDERER_JS = pathlib.Path("viewer/js/track-renderer.js").read_text()
MAIN_JS = pathlib.Path("viewer/js/main.js").read_text()
DASHBOARD_HTML = pathlib.Path("viewer/dashboard.html").read_text()


class TestTVDirector:
    def test_director_in_camera_js(self):
        assert "updateDirector" in CAMERA_JS
        assert "_directorTarget" in CAMERA_JS
        assert "_directorHoldUntil" in CAMERA_JS
        assert "_directorMode" in CAMERA_JS

    def test_director_target_getter(self):
        assert "getDirectorTarget" in CAMERA_JS

    def test_director_wired_in_main(self):
        assert "updateDirector" in MAIN_JS
        assert "getDirectorTarget" in MAIN_JS


class TestLabels:
    def test_car_abbrev_in_renderer(self):
        assert "getCarAbbrev" in CAR_RENDERER_JS

    def test_abbrev_uses_substring(self):
        assert "substring(0, 3)" in CAR_RENDERER_JS or "substr(0, 3)" in CAR_RENDERER_JS

    def test_car_color_in_labels(self):
        assert "car.color" in CAR_RENDERER_JS


class TestTrackOverlays:
    def test_sector_markers(self):
        assert "drawSectorMarkers" in TRACK_RENDERER_JS

    def test_drs_zones(self):
        assert "drawDRSZones" in TRACK_RENDERER_JS

    def test_sector_labels(self):
        assert "'S1'" in TRACK_RENDERER_JS
        assert "'S2'" in TRACK_RENDERER_JS


class TestHTML:
    def test_director_button(self):
        assert "director" in DASHBOARD_HTML.lower()


class TestArchCompliance:
    def test_camera_under_limits(self):
        assert len(CAMERA_JS.splitlines()) <= 220, "camera.js too long"

    def test_simulation_unchanged(self):
        sim = pathlib.Path("engine/simulation.py").read_text()
        assert len(sim.splitlines()) <= 400
        assert sim.count("\n    def ") + sim.count("\ndef ") <= 15
