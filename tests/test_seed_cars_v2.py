"""Tests for seed car v2 strategies — pit stops, fuel, lateral, engine modes."""

import importlib
import os
import sys

import pytest

from security.bot_scanner import scan_car_file

CARS_DIR = os.path.join(os.path.dirname(__file__), "..", "cars")
CAR_MODULES = ["gooseloose", "silky", "glasscanon", "brickhouse", "slipstream"]


def _load_car(name: str):
    """Import a car module by name, reloading if already cached."""
    mod_name = f"cars.{name}"
    if mod_name in sys.modules:
        return importlib.reload(sys.modules[mod_name])
    return importlib.import_module(mod_name)


def _make_state(**overrides) -> dict:
    """Build a minimal strategy state dict with sensible defaults."""
    base = {
        "speed": 180.0,
        "position": 3,
        "total_cars": 5,
        "lap": 5,
        "total_laps": 20,
        "tire_wear": 0.3,
        "boost_available": True,
        "boost_active": False,
        "curvature": 0.0,
        "nearby_cars": [],
        "distance": 5000.0,
        "track_length": 5000.0,
        "lateral": 0.0,
        "fuel_remaining": 50.0,
        "fuel_pct": 0.6,
        "tire_compound": "medium",
        "tire_age_laps": 5,
        "engine_mode": "standard",
        "pit_status": "racing",
        "pit_stops": 0,
        "gap_ahead_s": 1.5,
        "gap_behind_s": 2.0,
    }
    base.update(overrides)
    return base


# --- Cycle 1: All 5 cars import and have valid strategy functions ---


class TestCarImportsAndBasics:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_imports(self, name):
        mod = _load_car(name)
        assert hasattr(mod, "strategy")
        assert callable(mod.strategy)

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_has_required_attrs(self, name):
        mod = _load_car(name)
        for attr in ("CAR_NAME", "CAR_COLOR", "POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"):
            assert hasattr(mod, attr), f"{name} missing {attr}"

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_passes_bot_scanner(self, name):
        path = os.path.join(CARS_DIR, f"{name}.py")
        result = scan_car_file(path)
        assert result.passed, f"{name} failed scanner: {result.violations}"


# --- Cycle 2: Strategy returns correct fields ---


class TestStrategyReturns:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_strategy_returns_dict_with_throttle(self, name):
        mod = _load_car(name)
        result = mod.strategy(_make_state())
        assert isinstance(result, dict)
        assert "throttle" in result
        assert 0.0 <= result["throttle"] <= 1.0

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_strategy_returns_lateral_target(self, name):
        mod = _load_car(name)
        result = mod.strategy(_make_state())
        assert "lateral_target" in result
        assert -1.0 <= result["lateral_target"] <= 1.0

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_strategy_returns_engine_mode(self, name):
        mod = _load_car(name)
        result = mod.strategy(_make_state())
        assert "engine_mode" in result
        assert result["engine_mode"] in ("push", "standard", "conserve")


# --- Cycle 3: Pit stop behaviors ---


class TestPitStopStrategies:
    def test_gooseloose_pits_on_tire_wear(self):
        """GooseLoose pits when tire_wear > 0.70 (reactive, not lap_pct)."""
        mod = _load_car("gooseloose")
        state = _make_state(tire_wear=0.75, pit_stops=0, tire_compound="medium")
        result = mod.strategy(state)
        assert result.get("pit_request") is True
        assert result.get("tire_compound_request") == "hard"

    def test_gooseloose_no_pit_after_first(self):
        """GooseLoose should not pit again after first stop."""
        mod = _load_car("gooseloose")
        state = _make_state(lap=15, total_laps=20, pit_stops=1, tire_compound="hard",
                            tire_wear=0.3)
        result = mod.strategy(state)
        assert result.get("pit_request", False) is False

    def test_glasscanon_no_pit_when_tires_ok(self):
        """GlassCanon 0-stop preferred: no pit when tires are fine."""
        mod = _load_car("glasscanon")
        state = _make_state(tire_wear=0.5, pit_stops=0, tire_compound="hard")
        result = mod.strategy(state)
        assert result.get("pit_request", False) is False

    def test_brickhouse_pits_on_tire_wear(self):
        """BrickHouse 2-stop: pits based on tire_wear thresholds."""
        mod = _load_car("brickhouse")
        # First pit when softs worn past 0.65
        state1 = _make_state(tire_wear=0.70, pit_stops=0, tire_compound="soft")
        r1 = mod.strategy(state1)
        assert r1.get("pit_request") is True
        assert r1.get("tire_compound_request") == "medium"

        # Second pit when mediums worn past 0.70
        state2 = _make_state(tire_wear=0.75, pit_stops=1, tire_compound="medium")
        r2 = mod.strategy(state2)
        assert r2.get("pit_request") is True
        assert r2.get("tire_compound_request") == "hard"

    def test_brickhouse_no_third_pit(self):
        """BrickHouse should not pit a third time (low wear)."""
        mod = _load_car("brickhouse")
        state = _make_state(lap=18, total_laps=20, pit_stops=2, tire_compound="hard",
                            tire_wear=0.3)
        result = mod.strategy(state)
        assert result.get("pit_request", False) is False

    def test_silky_pits_on_tire_wear(self):
        """Silky pits when tire_wear > 0.72."""
        mod = _load_car("silky")
        state = _make_state(tire_wear=0.78, pit_stops=0, tire_compound="soft")
        result = mod.strategy(state)
        assert result.get("pit_request") is True
        assert result.get("tire_compound_request") == "medium"

    def test_slipstream_pits_with_gap_and_wear(self):
        """SlipStream pits when tire_wear > 0.68 and gap_ahead > 18."""
        mod = _load_car("slipstream")
        state = _make_state(tire_wear=0.72, pit_stops=0, tire_compound="medium",
                            gap_ahead_s=25.0)
        result = mod.strategy(state)
        assert result.get("pit_request") is True
        assert result.get("tire_compound_request") == "soft"


# --- Cycle 4: Engine mode behaviors ---


class TestEngineModes:
    def test_gooseloose_push_when_attacking(self):
        mod = _load_car("gooseloose")
        state = _make_state(position=3, gap_ahead_s=1.5)
        result = mod.strategy(state)
        assert result["engine_mode"] == "push"

    def test_gooseloose_conserve_when_leading(self):
        mod = _load_car("gooseloose")
        state = _make_state(position=1, gap_behind_s=5.0)
        result = mod.strategy(state)
        assert result["engine_mode"] == "conserve"

    def test_silky_conserve_engine(self):
        mod = _load_car("silky")
        state = _make_state(lap=3, total_laps=20, pit_stops=0)
        result = mod.strategy(state)
        assert result["engine_mode"] == "conserve"

    def test_glasscanon_always_push(self):
        mod = _load_car("glasscanon")
        for lap in [0, 5, 10, 15, 19]:
            state = _make_state(lap=lap, total_laps=20)
            result = mod.strategy(state)
            assert result["engine_mode"] == "push"

    def test_brickhouse_push_when_not_leading_conserve_when_p1(self):
        mod = _load_car("brickhouse")
        behind = mod.strategy(_make_state(position=2, tire_wear=0.3))
        assert behind["engine_mode"] == "push"
        leading = mod.strategy(_make_state(position=1, tire_wear=0.3))
        assert leading["engine_mode"] == "conserve"

    def test_slipstream_push_on_fresh_softs(self):
        mod = _load_car("slipstream")
        state = _make_state(lap=14, total_laps=20, pit_stops=1,
                            tire_compound="soft", tire_age_laps=2,
                            gap_ahead_s=2.0)
        result = mod.strategy(state)
        assert result["engine_mode"] == "push"


# --- Cycle 5: Lateral behaviors ---


class TestLateralBehaviors:
    def test_gooseloose_blocks_when_car_close_behind(self):
        mod = _load_car("gooseloose")
        state = _make_state(
            gap_behind_s=0.5,
            nearby_cars=[{"name": "Rival", "distance_ahead": -10,
                          "speed": 190, "lateral": 0.5}],
        )
        result = mod.strategy(state)
        # Should move to block
        assert result["lateral_target"] != 0.0

    def test_silky_inside_line_in_corners(self):
        mod = _load_car("silky")
        # Positive curvature -> inside line (-1)
        state = _make_state(curvature=0.3)
        result = mod.strategy(state)
        assert result["lateral_target"] < 0.0

    def test_glasscanon_blocks_on_straights(self):
        mod = _load_car("glasscanon")
        state = _make_state(
            curvature=0.0,
            gap_behind_s=0.5,
            nearby_cars=[{"name": "Rival", "distance_ahead": -10,
                          "speed": 190, "lateral": 0.5}],
        )
        result = mod.strategy(state)
        assert result["lateral_target"] != 0.0

    def test_slipstream_follows_car_ahead(self):
        mod = _load_car("slipstream")
        state = _make_state(
            nearby_cars=[{"name": "Leader", "distance_ahead": 20,
                          "speed": 180, "lateral": -0.5}],
        )
        result = mod.strategy(state)
        # Should follow the car ahead's lateral position
        assert result["lateral_target"] < 0.0


# --- Cycle 6: File size constraint ---


class TestFileSize:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_file_under_100_lines(self, name):
        path = os.path.join(CARS_DIR, f"{name}.py")
        with open(path) as f:
            line_count = sum(1 for _ in f)
        assert line_count < 100, f"{name}.py is {line_count} lines (max 100)"
