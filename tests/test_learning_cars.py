"""Tests for cross-race learning in seed cars (T4.5)."""

import json
import os
import pytest

from security.bot_scanner import scan_car_file
from tests.helpers import CAR_MODULES, CAR_NAME_MAP, _load_car, _make_state

CARS_DIR = os.path.join(os.path.dirname(__file__), "..", "cars")


# --- Cycle 1: All cars import json and have learning infrastructure ---


class TestLearningInfrastructure:
    """All 5 cars have json import and data loading/saving functions."""

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_imports_json(self, name):
        """Each car module has json available."""
        mod = _load_car(name)
        # Module must have _ensure_data and _save helpers
        assert hasattr(mod, "_ensure_data"), f"{name} missing _ensure_data"
        assert hasattr(mod, "_save"), f"{name} missing _save"

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_has_data_cache(self, name):
        """Each car has module-level _data and _last_race variables."""
        mod = _load_car(name)
        assert hasattr(mod, "_data")
        assert hasattr(mod, "_last_race")

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_strategy_returns_dict_with_data_file(self, name):
        """Strategy still returns valid dict when data_file is provided."""
        mod = _load_car(name)
        car_name = CAR_NAME_MAP[name]
        state = _make_state(
            data_file=f"cars/data/{car_name}.json",
            track_name="monaco",
        )
        result = mod.strategy(state)
        assert isinstance(result, dict)
        assert "throttle" in result

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_strategy_works_without_data_file(self, name):
        """Strategy works when data_file is None (non-tournament)."""
        mod = _load_car(name)
        state = _make_state(data_file=None, track_name=None)
        result = mod.strategy(state)
        assert isinstance(result, dict)


# --- Cycle 2: Bot scanner passes and file size ---


class TestScannerAndSize:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_passes_bot_scanner(self, name):
        """All cars pass bot_scanner with json and gated open."""
        path = os.path.join(CARS_DIR, f"{name}.py")
        result = scan_car_file(path)
        assert result.passed, f"{name} scanner: {result.violations}"

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_file_under_100_lines(self, name):
        """All car files stay under 100 lines."""
        path = os.path.join(CARS_DIR, f"{name}.py")
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) <= 100, f"{name} has {len(lines)} lines (max 100)"


# --- Cycle 3: BrickHouse learns pit threshold ---


class TestBrickHouseLearning:
    def test_brickhouse_saves_data_on_last_lap(self):
        """BrickHouse writes threshold data on last lap."""
        os.makedirs("cars/data", exist_ok=True)
        path = "cars/data/BrickHouse.json"
        try:
            # Remove any existing data
            if os.path.exists(path):
                os.unlink(path)
            mod = _load_car("brickhouse")
            # Simulate calling strategy on last lap with track_name
            state = _make_state(
                lap=19, total_laps=20, position=2,
                tire_wear=0.5, pit_stops=1,
                data_file=path, track_name="monaco",
            )
            mod.strategy(state)
            assert os.path.exists(path), "Data file not created"
            with open(path) as f:
                data = json.load(f)
            assert "monaco" in data
            assert "best_threshold" in data["monaco"] or "best_position" in data["monaco"]
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_brickhouse_data_contains_threshold(self):
        """BrickHouse data tracks pit wear threshold per track."""
        os.makedirs("cars/data", exist_ok=True)
        path = "cars/data/BrickHouse.json"
        try:
            if os.path.exists(path):
                os.unlink(path)
            mod = _load_car("brickhouse")
            state = _make_state(
                lap=19, total_laps=20, position=3,
                tire_wear=0.5, pit_stops=2,
                data_file=path, track_name="monaco",
            )
            mod.strategy(state)
            with open(path) as f:
                data = json.load(f)
            track_data = data.get("monaco", {})
            assert "best_threshold" in track_data
        finally:
            if os.path.exists(path):
                os.unlink(path)


# --- Cycle 4: GlassCanon learns stop strategy ---


class TestGlassCanonLearning:
    def test_glasscanon_tracks_stop_strategy(self):
        """GlassCanon records 0-stop vs 1-stop average positions."""
        os.makedirs("cars/data", exist_ok=True)
        path = "cars/data/GlassCanon.json"
        try:
            if os.path.exists(path):
                os.unlink(path)
            mod = _load_car("glasscanon")
            state = _make_state(
                lap=19, total_laps=20, position=2,
                tire_wear=0.5, pit_stops=0,
                data_file=path, track_name="monza",
            )
            mod.strategy(state)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "monza" in data
            track = data["monza"]
            assert "0stop_avg_pos" in track or "races" in track
        finally:
            if os.path.exists(path):
                os.unlink(path)


# --- Cycle 5: Silky learns compound effectiveness ---


class TestSilkyLearning:
    def test_silky_tracks_compound_order(self):
        """Silky records soft-first vs medium-first average positions."""
        os.makedirs("cars/data", exist_ok=True)
        path = "cars/data/Silky.json"
        try:
            if os.path.exists(path):
                os.unlink(path)
            mod = _load_car("silky")
            state = _make_state(
                lap=19, total_laps=20, position=2,
                tire_wear=0.4, pit_stops=1,
                tire_compound="medium",
                data_file=path, track_name="spa",
            )
            mod.strategy(state)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "spa" in data
        finally:
            if os.path.exists(path):
                os.unlink(path)


# --- Cycle 6: GooseLoose learns opponent patterns ---


class TestGooseLooseLearning:
    def test_gooseloose_tracks_opponents(self):
        """GooseLoose records opponent speed data."""
        os.makedirs("cars/data", exist_ok=True)
        path = "cars/data/GooseLoose.json"
        try:
            if os.path.exists(path):
                os.unlink(path)
            mod = _load_car("gooseloose")
            nearby = [
                {"name": "Silky", "distance_ahead": 10, "speed": 165, "lateral": 0},
                {"name": "GlassCanon", "distance_ahead": -5, "speed": 180, "lateral": 0},
            ]
            state = _make_state(
                lap=19, total_laps=20, position=2,
                nearby_cars=nearby,
                data_file=path, track_name="monaco",
            )
            mod.strategy(state)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "monaco" in data
        finally:
            if os.path.exists(path):
                os.unlink(path)


# --- Cycle 7: SlipStream learns draft effectiveness ---


class TestSlipStreamLearning:
    def test_slipstream_tracks_drafting(self):
        """SlipStream records draft vs no-draft position data."""
        os.makedirs("cars/data", exist_ok=True)
        path = "cars/data/SlipStream.json"
        try:
            if os.path.exists(path):
                os.unlink(path)
            mod = _load_car("slipstream")
            state = _make_state(
                lap=19, total_laps=20, position=3,
                gap_ahead_s=2.0,
                data_file=path, track_name="monza",
            )
            mod.strategy(state)
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert "monza" in data
        finally:
            if os.path.exists(path):
                os.unlink(path)


# --- Data file size check ---


class TestDataFileSize:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_data_file_under_100kb(self, name):
        """Data files stay under 100KB."""
        car_name = CAR_NAME_MAP[name]
        path = f"cars/data/{car_name}.json"
        if os.path.exists(path):
            size = os.path.getsize(path)
            assert size < 100_000, f"{car_name} data is {size} bytes"
