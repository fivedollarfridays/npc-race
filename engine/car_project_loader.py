"""Multi-file car project loader for NPC Race.

Loads a directory as a car project: car.py for metadata/stats,
optional per-part .py files, and optional helpers/ directory.
"""

from __future__ import annotations

import importlib.util
import os

from .parts_api import CAR_PARTS, get_defaults

STAT_FIELDS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]
METADATA_FIELDS = ["CAR_NAME", "CAR_COLOR"] + STAT_FIELDS


def _load_module(filepath: str, module_name: str):
    """Load a Python file as a module via importlib.util."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _collect_source(project_dir: str) -> str:
    """Read and concatenate all .py files in the project directory."""
    sources: list[str] = []
    for filename in sorted(os.listdir(project_dir)):
        if filename.endswith(".py"):
            filepath = os.path.join(project_dir, filename)
            with open(filepath, encoding="utf-8") as f:
                sources.append(f.read())
    # Also include helpers/ subdirectory if present
    helpers_dir = os.path.join(project_dir, "helpers")
    if os.path.isdir(helpers_dir):
        for filename in sorted(os.listdir(helpers_dir)):
            if filename.endswith(".py"):
                filepath = os.path.join(helpers_dir, filename)
                with open(filepath, encoding="utf-8") as f:
                    sources.append(f.read())
    return "\n".join(sources)


def load_car_project(project_dir: str) -> dict:
    """Load a car project directory and return a car dict.

    Raises FileNotFoundError if car.py is missing.
    """
    car_py = os.path.join(project_dir, "car.py")
    if not os.path.isfile(car_py):
        raise FileNotFoundError(
            f"car.py not found in project directory: {project_dir}"
        )

    mod = _load_module(car_py, "car")

    car: dict = {}
    for field in METADATA_FIELDS:
        car[field] = getattr(mod, field)

    # Load part functions from per-part files or use defaults
    part_defaults = get_defaults()
    car["parts"] = {}
    loaded_parts: list[str] = []

    for part_name in CAR_PARTS:
        part_file = os.path.join(project_dir, f"{part_name}.py")
        if os.path.isfile(part_file):
            part_mod = _load_module(part_file, part_name)
            func = getattr(part_mod, part_name, None)
            if callable(func):
                car["parts"][part_name] = func
                loaded_parts.append(part_name)
                continue
        car["parts"][part_name] = part_defaults[part_name]

    car["_loaded_parts"] = loaded_parts

    # Concatenate source of all .py files for reliability scoring
    car["_source"] = _collect_source(project_dir)

    # Hardware specs with defaults
    car["engine_spec"] = getattr(mod, "ENGINE_SPEC", "v6_1000hp")
    car["aero_spec"] = getattr(mod, "AERO_SPEC", "medium_downforce")
    car["chassis_spec"] = getattr(mod, "CHASSIS_SPEC", "standard")

    return car
