"""T37.2 — Verify default_project template is excluded from race loading.

The default_project directory is a starter template for new players.
It must exist on disk but must NOT be loaded as a racing car.
"""

import os
import pathlib

import pytest

from engine.car_loader import load_all_cars

CARS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "cars")


@pytest.fixture(scope="module")
def all_cars():
    """Load all cars once for the module."""
    return load_all_cars(CARS_DIR)


# --- Cycle 1: Template directory exists on disk ---


def test_default_project_dir_exists():
    """The default_project template directory still exists on disk."""
    assert os.path.isdir(os.path.join(CARS_DIR, "default_project"))


# --- Cycle 2: Exclusion from loading ---


def test_load_all_cars_excludes_template(all_cars):
    """load_all_cars returns 19 cars (template excluded)."""
    assert len(all_cars) == 19


def test_no_car_named_from_template_dir(all_cars):
    """No loaded car comes from the default_project directory."""
    for car in all_cars:
        car_file = car.get("file", "")
        assert "default_project" not in car_file, (
            f"Car '{car['CAR_NAME']}' was loaded from template dir: {car_file}"
        )
