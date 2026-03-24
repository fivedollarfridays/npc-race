"""End-to-end onboarding flow: init -> run -> submit -> leaderboard."""

import json
import os
import shutil

import pytest

from cli.main import main

pytestmark = pytest.mark.smoke

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_DIR = os.path.join(REPO_ROOT, "cars")


# --- Helpers ---


def _cleanup_paths(*paths: str) -> None:
    """Remove files and directories, ignoring missing ones."""
    for p in paths:
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.isfile(p):
            os.remove(p)


# --- Tests ---


def test_init_creates_unique_car():
    """npcrace init creates a car dir with PascalCase CAR_NAME."""
    name = "zzz-test-flow-car"
    target = os.path.join(CARS_DIR, name)
    try:
        main(["init", name])
        car_py = os.path.join(target, "car.py")
        assert os.path.isfile(car_py), "car.py not created"
        with open(car_py) as f:
            content = f.read()
        assert 'CAR_NAME = "ZzzTestFlowCar"' in content
    finally:
        _cleanup_paths(target)


def _run_race_to_tmp(replay_file: str) -> None:
    """Run a 1-lap monza race writing output to the given replay path."""
    main([
        "run",
        "--car-dir", "cars",
        "--track", "monza",
        "--laps", "1",
        "--output", replay_file,
        "--no-browser",
    ])


def _assert_results_valid(results_file: str, expected_car: str) -> None:
    """Verify results.json has 20 unique cars including *expected_car*."""
    assert os.path.isfile(results_file), "results.json not created"
    with open(results_file) as f:
        results = json.load(f)
    cars_in_results = results.get("cars", [])
    assert len(cars_in_results) == 20, (
        f"Expected 20 cars (19 rivals + 1 player), got {len(cars_in_results)}"
    )
    car_names = [c["name"] for c in cars_in_results]
    assert expected_car in car_names, (
        f"{expected_car} not found in results: {car_names}"
    )
    assert len(car_names) == len(set(car_names)), (
        f"Duplicate car names found: {car_names}"
    )


def test_full_onboarding_flow(capsys, tmp_path):
    """Gate test: init -> run -> submit -> leaderboard in sequence."""
    name = "zzz-test-flow"
    pascal_name = "ZzzTestFlow"
    target = os.path.join(CARS_DIR, name)
    results_file = os.path.join(str(tmp_path), "results.json")
    lap_summary = os.path.join(str(tmp_path), "lap_summary.json")
    lb_file = os.path.join(str(tmp_path), "lb.json")
    replay_file = os.path.join(str(tmp_path), "replay.json")

    try:
        # Step 1: init
        main(["init", name])
        car_py = os.path.join(target, "car.py")
        assert os.path.isfile(car_py)
        with open(car_py) as f:
            assert f'CAR_NAME = "{pascal_name}"' in f.read()

        # Step 2: run a 1-lap race
        _run_race_to_tmp(replay_file)
        _assert_results_valid(results_file, pascal_name)

        # Step 3: submit
        capsys.readouterr()
        main(["submit", results_file])
        out = capsys.readouterr().out
        assert "verified" in out.lower(), f"Expected 'verified': {out}"

        # Step 4: leaderboard --add
        capsys.readouterr()
        main(["leaderboard", "--add", results_file, "--file", lb_file])
        out = capsys.readouterr().out
        assert pascal_name in out, f"{pascal_name} not in leaderboard: {out}"

    finally:
        _cleanup_paths(target, results_file, lap_summary, lb_file, replay_file)


def test_league_output_is_quiet(capsys, tmp_path):
    """Default race output shows 'cars validated' but not 'Advisory'."""
    replay_file = os.path.join(str(tmp_path), "replay.json")
    try:
        main([
            "run",
            "--car-dir", "cars",
            "--track", "monza",
            "--laps", "1",
            "--output", replay_file,
            "--no-browser",
        ])
        out = capsys.readouterr().out
        assert "cars validated" in out, f"Expected 'cars validated' in: {out}"
        assert "Advisory" not in out, (
            f"Advisory should be suppressed in non-verbose mode: {out}"
        )
    finally:
        results_file = os.path.join(str(tmp_path), "results.json")
        lap_file = os.path.join(str(tmp_path), "lap_summary.json")
        _cleanup_paths(replay_file, results_file, lap_file)


def test_no_default_project_on_grid(tmp_path):
    """No car named 'DefaultProject' should appear in race results."""
    replay_file = os.path.join(str(tmp_path), "replay.json")
    results_file = os.path.join(str(tmp_path), "results.json")
    try:
        main([
            "run",
            "--car-dir", "cars",
            "--track", "monza",
            "--laps", "1",
            "--output", replay_file,
            "--no-browser",
        ])
        with open(results_file) as f:
            results = json.load(f)
        car_names = [c["name"] for c in results.get("cars", [])]
        assert "DefaultProject" not in car_names, (
            f"DefaultProject should not be on grid: {car_names}"
        )
    finally:
        lap_file = os.path.join(str(tmp_path), "lap_summary.json")
        _cleanup_paths(replay_file, results_file, lap_file)
