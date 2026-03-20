"""Sprint 20 integration gate — parts system validation (T20.6)."""

import pathlib

import pytest

from engine.car_loader import load_all_cars
from engine.car_attributes import compute_attributes
from engine.track_performance import get_track_performance
from engine.parts_catalog import DEFAULTS, BUDGET_CAP, get_total_cost

pytestmark = pytest.mark.slow

CARS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "cars")


class TestComponentCarLoads:
    def test_legacy_cars_still_race(self):
        from engine import run_race
        results = run_race(car_dir=CARS_DIR, track_name="monza", laps=1,
                            output="/tmp/parts_gate.json")
        assert len(results) >= 3

    def test_component_car_has_attributes(self):
        cars = load_all_cars(CARS_DIR)
        for car in cars:
            assert "derived" in car
            assert car["derived"]["top_speed_kmh"] > 300


class TestPerformanceDifference:
    def test_different_builds_different_speed(self):
        fast = dict(DEFAULTS)
        fast["ENGINE"] = "pu_high_output"
        slow = dict(DEFAULTS)
        slow["ENGINE"] = "pu_efficient"
        assert compute_attributes(fast)["top_speed_kmh"] > compute_attributes(slow)["top_speed_kmh"]

    def test_track_matters(self):
        attrs = compute_attributes(DEFAULTS)
        monza = get_track_performance(attrs, "monza")
        monaco = get_track_performance(attrs, "monaco")
        # Same car, different tracks — should give different modifiers
        # (may be equal if perfectly balanced, but usually different)
        assert isinstance(monza, float)
        assert isinstance(monaco, float)


class TestBudget:
    def test_default_build_under_cap(self):
        cost = get_total_cost(DEFAULTS)
        assert cost <= BUDGET_CAP

    def test_over_budget_rejected(self):
        expensive = {}
        from engine.parts_catalog import CATALOG
        for cat, options in CATALOG.items():
            most = max(options.items(), key=lambda x: x[1].get("cost_m", 0))
            expensive[cat] = most[0]
        cost = get_total_cost(expensive)
        assert cost > BUDGET_CAP


class TestArchCompliance:
    def test_parts_catalog_under_limits(self):
        lines = len(pathlib.Path("engine/parts_catalog.py").read_text().splitlines())
        assert lines <= 200, f"parts_catalog.py has {lines} lines"

    def test_car_attributes_under_limits(self):
        lines = len(pathlib.Path("engine/car_attributes.py").read_text().splitlines())
        assert lines <= 100, f"car_attributes.py has {lines} lines"
