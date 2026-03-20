"""Tests for component-based car loader (T20.5)."""

import os
import tempfile

from engine.car_loader import load_car, load_all_cars

CARS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars")


class TestComponentLoader:
    def test_legacy_car_still_works(self):
        """Old POWER/GRIP cars load without error."""
        cars = load_all_cars(CARS_DIR)
        assert len(cars) >= 3

    def test_legacy_auto_converts(self):
        """Legacy cars get component selections."""
        cars = load_all_cars(CARS_DIR)
        for car in cars:
            assert "components" in car
            assert "ENGINE" in car["components"]

    def test_derived_attrs_in_car_dict(self):
        """Loaded cars have derived performance attributes."""
        cars = load_all_cars(CARS_DIR)
        for car in cars:
            assert "derived" in car
            assert "top_speed_kmh" in car["derived"]
            assert "low_speed_grip" in car["derived"]
            assert "braking_g" in car["derived"]

    def test_load_component_car(self):
        """Car with ENGINE/AERO components loads correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", dir=CARS_DIR,
                                          delete=False, prefix="test_comp_") as f:
            f.write('''
CAR_NAME = "TestComp"
CAR_COLOR = "#00ff00"
POWER = 20
GRIP = 20
WEIGHT = 20
AERO = 20
BRAKES = 20
ENGINE = "pu_high_output"
AERO_PKG = "aero_low_drag"

def strategy(state):
    return {}
''')
            path = f.name
        try:
            car = load_car(path)
            assert car["CAR_NAME"] == "TestComp"
            assert "derived" in car
            assert car["components"]["ENGINE"] == "pu_high_output"
        finally:
            os.unlink(path)

    def test_different_builds_different_attrs(self):
        """Different legacy cars get different derived attributes."""
        cars = load_all_cars(CARS_DIR)
        if len(cars) >= 2:
            a, b = cars[0]["derived"], cars[1]["derived"]
            # At least one attribute should differ
            differs = any(a.get(k) != b.get(k) for k in a)
            assert differs
