"""Tests for reactive car strategies — tire_wear-based pitting, no fixed lap_pct."""

import os

import pytest

from security.bot_scanner import scan_car_file
from tests.helpers import CAR_MODULES, _load_car, _make_state

CARS_DIR = os.path.join(os.path.dirname(__file__), "..", "cars")


# --- Cycle 1: All cars import and pass bot_scanner ---


class TestImportsAndScanner:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_imports_and_has_strategy(self, name):
        mod = _load_car(name)
        assert hasattr(mod, "strategy")
        assert callable(mod.strategy)

    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_passes_bot_scanner(self, name):
        path = os.path.join(CARS_DIR, f"{name}.py")
        result = scan_car_file(path)
        assert result.passed, f"{name} failed scanner: {result.violations}"


# --- Cycle 2: Reactive pit decisions (tire_wear, NOT lap_pct) ---


class TestReactivePitting:
    def test_brickhouse_pits_on_high_tire_wear(self):
        """BrickHouse pits when tire_wear > 0.65, not at fixed lap %."""
        mod = _load_car("brickhouse")
        # High tire wear on softs, first stint — should pit
        state = _make_state(
            tire_wear=0.70, pit_stops=0, tire_compound="soft",
            lap=3, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is True
        assert result["tire_compound_request"] == "medium"

    def test_brickhouse_no_pit_when_tires_fresh(self):
        """BrickHouse should NOT pit when tires are fresh, even late in race."""
        mod = _load_car("brickhouse")
        state = _make_state(
            tire_wear=0.30, pit_stops=0, tire_compound="soft",
            lap=15, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is False

    def test_brickhouse_second_pit_on_mediums(self):
        """BrickHouse second stop when mediums wear past 0.70."""
        mod = _load_car("brickhouse")
        state = _make_state(
            tire_wear=0.75, pit_stops=1, tire_compound="medium",
            lap=10, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is True
        assert result["tire_compound_request"] == "hard"

    def test_brickhouse_emergency_pit(self):
        """BrickHouse emergency pit at 0.85 regardless of stint."""
        mod = _load_car("brickhouse")
        state = _make_state(
            tire_wear=0.90, pit_stops=0, tire_compound="soft",
            lap=2, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is True

    def test_glasscanon_pits_on_extreme_wear(self):
        """GlassCanon emergency pits when tire_wear > 0.80."""
        mod = _load_car("glasscanon")
        state = _make_state(
            tire_wear=0.85, pit_stops=0, tire_compound="hard",
            lap=15, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is True

    def test_glasscanon_no_pit_when_tires_ok(self):
        """GlassCanon prefers 0-stop when tires are fine."""
        mod = _load_car("glasscanon")
        state = _make_state(
            tire_wear=0.50, pit_stops=0, tire_compound="hard",
            lap=15, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is False

    def test_gooseloose_pits_on_tire_wear(self):
        """GooseLoose pits when tire_wear > 0.70."""
        mod = _load_car("gooseloose")
        state = _make_state(
            tire_wear=0.75, pit_stops=0, tire_compound="medium",
            lap=5, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is True
        assert result["tire_compound_request"] == "hard"

    def test_gooseloose_no_pit_when_fresh(self):
        """GooseLoose does NOT pit when tires are fine."""
        mod = _load_car("gooseloose")
        state = _make_state(
            tire_wear=0.40, pit_stops=0, tire_compound="medium",
            lap=10, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is False

    def test_silky_pits_on_tire_wear(self):
        """Silky pits when tire_wear > 0.72."""
        mod = _load_car("silky")
        state = _make_state(
            tire_wear=0.78, pit_stops=0, tire_compound="soft",
            lap=5, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is True
        assert result["tire_compound_request"] == "medium"

    def test_slipstream_pits_with_gap(self):
        """SlipStream pits when tire_wear > 0.68 AND gap_ahead_s > 18."""
        mod = _load_car("slipstream")
        state = _make_state(
            tire_wear=0.72, pit_stops=0, tire_compound="medium",
            gap_ahead_s=25.0, lap=8, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is True
        assert result["tire_compound_request"] == "soft"

    def test_slipstream_no_pit_without_gap(self):
        """SlipStream does NOT pit when gap is too small even with worn tires."""
        mod = _load_car("slipstream")
        state = _make_state(
            tire_wear=0.72, pit_stops=0, tire_compound="medium",
            gap_ahead_s=5.0, lap=8, total_laps=20,
        )
        result = mod.strategy(state)
        assert result["pit_request"] is False


# --- Cycle 3: No car uses fixed lap_pct for pit decisions ---


class TestNoFixedLapPct:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_no_lap_pct_in_source(self, name):
        """No car should compute lap_pct for pit timing."""
        path = os.path.join(CARS_DIR, f"{name}.py")
        with open(path) as f:
            source = f.read()
        # lap_pct used for pit decisions is banned
        assert "lap_pct" not in source, (
            f"{name}.py still uses lap_pct — pit timing must be tire_wear-based"
        )


# --- Cycle 4: Engine mode behaviors ---


class TestReactiveEngineModes:
    def test_gooseloose_conserve_when_leading(self):
        """GooseLoose conserves when P1 with big gap behind."""
        mod = _load_car("gooseloose")
        state = _make_state(position=1, gap_behind_s=5.0)
        result = mod.strategy(state)
        assert result["engine_mode"] == "conserve"

    def test_gooseloose_push_when_close_to_car_ahead(self):
        """GooseLoose pushes when gap_ahead_s < 2.0 (attacking)."""
        mod = _load_car("gooseloose")
        state = _make_state(position=3, gap_ahead_s=1.5)
        result = mod.strategy(state)
        assert result["engine_mode"] == "push"

    def test_gooseloose_standard_otherwise(self):
        """GooseLoose uses standard when not leading or attacking."""
        mod = _load_car("gooseloose")
        state = _make_state(position=2, gap_ahead_s=5.0, gap_behind_s=1.0)
        result = mod.strategy(state)
        assert result["engine_mode"] == "standard"

    def test_brickhouse_push_when_not_leading(self):
        """BrickHouse pushes when position > 1."""
        mod = _load_car("brickhouse")
        state = _make_state(position=2, tire_wear=0.3)
        result = mod.strategy(state)
        assert result["engine_mode"] == "push"

    def test_brickhouse_conserve_when_leading(self):
        """BrickHouse conserves when leading."""
        mod = _load_car("brickhouse")
        state = _make_state(position=1, tire_wear=0.3)
        result = mod.strategy(state)
        assert result["engine_mode"] == "conserve"

    def test_silky_conserve_first_stint(self):
        """Silky conserves engine during first stint (soft tires)."""
        mod = _load_car("silky")
        state = _make_state(pit_stops=0, tire_compound="soft")
        result = mod.strategy(state)
        assert result["engine_mode"] == "conserve"

    def test_silky_standard_second_stint(self):
        """Silky uses standard engine on mediums."""
        mod = _load_car("silky")
        state = _make_state(pit_stops=1, tire_compound="medium")
        result = mod.strategy(state)
        assert result["engine_mode"] == "standard"

    def test_glasscanon_always_push(self):
        """GlassCanon always pushes."""
        mod = _load_car("glasscanon")
        result = mod.strategy(_make_state())
        assert result["engine_mode"] == "push"

    def test_slipstream_push_on_fresh_softs_close(self):
        """SlipStream pushes on fresh softs when gap_ahead < 3."""
        mod = _load_car("slipstream")
        state = _make_state(
            pit_stops=1, tire_compound="soft", gap_ahead_s=2.0,
        )
        result = mod.strategy(state)
        assert result["engine_mode"] == "push"


# --- Cycle 5: Lateral behaviors ---


class TestReactiveLateral:
    def test_silky_blocks_on_straights_when_pressed(self):
        """Silky blocks on straights when gap_behind_s < 1.0."""
        mod = _load_car("silky")
        state = _make_state(
            curvature=0.02,  # straight
            gap_behind_s=0.5,
            nearby_cars=[{"name": "Rival", "distance_ahead": -10,
                          "speed": 190, "lateral": 0.5}],
        )
        result = mod.strategy(state)
        # Should NOT be the default inside line on a straight
        # Should block (match rival's lateral)
        assert result["lateral_target"] != 0.0

    def test_silky_inside_in_corners(self):
        """Silky takes inside line in corners."""
        mod = _load_car("silky")
        state = _make_state(curvature=0.3, gap_behind_s=5.0)
        result = mod.strategy(state)
        assert result["lateral_target"] < 0.0  # inside line

    def test_slipstream_follows_car_ahead(self):
        """SlipStream follows car ahead laterally when gap < 5.0."""
        mod = _load_car("slipstream")
        state = _make_state(
            gap_ahead_s=3.0,
            nearby_cars=[{"name": "Leader", "distance_ahead": 20,
                          "speed": 180, "lateral": -0.7}],
        )
        result = mod.strategy(state)
        assert result["lateral_target"] == pytest.approx(-0.7, abs=0.1)

    def test_slipstream_center_when_no_car_close(self):
        """SlipStream centers when no car ahead within 5s."""
        mod = _load_car("slipstream")
        state = _make_state(
            gap_ahead_s=10.0,
            nearby_cars=[{"name": "Leader", "distance_ahead": 200,
                          "speed": 180, "lateral": -0.7}],
        )
        result = mod.strategy(state)
        assert result["lateral_target"] == pytest.approx(0.0, abs=0.1)

    def test_gooseloose_inside_in_corners(self):
        """GooseLoose takes inside line in corners (curvature > 0.1)."""
        mod = _load_car("gooseloose")
        state = _make_state(curvature=0.2, gap_behind_s=5.0)
        result = mod.strategy(state)
        assert result["lateral_target"] == pytest.approx(-0.5, abs=0.2)

    def test_gooseloose_defends_on_straights(self):
        """GooseLoose defends on straights when gap_behind < 1.0."""
        mod = _load_car("gooseloose")
        state = _make_state(
            curvature=0.02,
            gap_behind_s=0.5,
            nearby_cars=[{"name": "R", "distance_ahead": -10,
                          "speed": 190, "lateral": 0.5}],
        )
        result = mod.strategy(state)
        assert result["lateral_target"] != 0.0


# --- Cycle 6: Throttle behaviors ---


class TestThrottleBehaviors:
    def test_brickhouse_cautious_in_corners(self):
        """BrickHouse uses 0.75 throttle in corners."""
        mod = _load_car("brickhouse")
        state = _make_state(curvature=0.2)
        result = mod.strategy(state)
        assert result["throttle"] == pytest.approx(0.75, abs=0.05)

    def test_glasscanon_throttle_in_tight_corners(self):
        """GlassCanon uses 0.85 in tight corners, not full send."""
        mod = _load_car("glasscanon")
        state = _make_state(curvature=0.15)
        result = mod.strategy(state)
        assert result["throttle"] == pytest.approx(0.85, abs=0.05)

    def test_silky_high_corner_throttle(self):
        """Silky uses 0.9 in corners (grip handles it)."""
        mod = _load_car("silky")
        state = _make_state(curvature=0.2)
        result = mod.strategy(state)
        assert result["throttle"] == pytest.approx(0.9, abs=0.05)

    def test_gooseloose_corner_throttle(self):
        """GooseLoose uses 0.75 in curves."""
        mod = _load_car("gooseloose")
        state = _make_state(curvature=0.2)
        result = mod.strategy(state)
        assert result["throttle"] == pytest.approx(0.75, abs=0.05)

    def test_slipstream_corner_throttle(self):
        """SlipStream uses 0.7 in corners."""
        mod = _load_car("slipstream")
        state = _make_state(curvature=0.2)
        result = mod.strategy(state)
        assert result["throttle"] == pytest.approx(0.7, abs=0.05)


# --- Cycle 7: File size ---


class TestFileConstraints:
    @pytest.mark.parametrize("name", CAR_MODULES)
    def test_car_file_under_100_lines(self, name):
        path = os.path.join(CARS_DIR, f"{name}.py")
        with open(path) as f:
            line_count = sum(1 for _ in f)
        assert line_count < 100, f"{name}.py is {line_count} lines (max 100)"
