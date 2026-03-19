"""Tests for car development system (T16.3)."""
from engine.car_development import (
    create_dev_state, award_dev_points, apply_upgrades,
    apply_dev_to_car, STAT_BUDGET,
)


def _mock_car():
    return {"CAR_NAME": "TestCar", "POWER": 18, "GRIP": 18, "WEIGHT": 18, "AERO": 18, "BRAKES": 18}


class TestCreateDevState:
    def test_create_dev_state(self):
        ds = create_dev_state(_mock_car())
        assert ds["dev_points"] == 0
        assert all(v == 0 for v in ds["upgrades"].values())


class TestAwardDevPoints:
    def test_award_points_p1(self):
        ds = create_dev_state(_mock_car())
        award_dev_points(ds, 1)
        assert ds["dev_points"] == 10

    def test_award_points_dnf(self):
        ds = create_dev_state(_mock_car())
        award_dev_points(ds, 15)
        assert ds["dev_points"] == 0

    def test_cumulative_dev_points(self):
        ds = create_dev_state(_mock_car())
        award_dev_points(ds, 1)
        award_dev_points(ds, 3)
        assert ds["dev_points"] == 10 + 5


class TestApplyUpgrades:
    def test_apply_upgrade(self):
        ds = create_dev_state(_mock_car())
        ds["dev_points"] = 10
        apply_upgrades(ds, {"POWER": 1})
        assert ds["upgrades"]["POWER"] == 1
        assert ds["dev_points"] == 5

    def test_insufficient_points(self):
        ds = create_dev_state(_mock_car())
        ds["dev_points"] = 2
        apply_upgrades(ds, {"POWER": 1})
        assert ds["upgrades"]["POWER"] == 0  # can't afford

    def test_budget_cap_enforced(self):
        ds = create_dev_state(_mock_car())
        ds["dev_points"] = 100
        apply_upgrades(ds, {"POWER": 5})  # would make total 105
        total = sum(ds["base_stats"][s] + ds["upgrades"][s] for s in ds["upgrades"])
        assert total <= STAT_BUDGET

    def test_per_stat_cap(self):
        ds = create_dev_state(_mock_car())
        ds["dev_points"] = 200
        apply_upgrades(ds, {"POWER": 15})
        assert ds["upgrades"]["POWER"] <= 10


class TestApplyDevToCar:
    def test_apply_dev_to_car(self):
        car = _mock_car()
        ds = create_dev_state(car)
        ds["upgrades"]["POWER"] = 3
        upgraded = apply_dev_to_car(car, ds)
        assert upgraded["POWER"] == 21  # 18 base + 3 upgrade
        assert upgraded["GRIP"] == 18  # unchanged
