"""Integration gate — full game flow from init to leaderboard.

Verifies the end-to-end player experience:
init -> validate -> race -> edit -> race again -> submit -> leaderboard
"""

import json
import os
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_DIR = os.path.join(REPO_ROOT, "cars")
GATE_CAR = "zzz-gate"
GATE_DIR = os.path.join(CARS_DIR, GATE_CAR)


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run npcrace CLI command and return result."""
    return subprocess.run(
        ["npcrace"] + args,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        **kwargs,
    )


@pytest.fixture(autouse=True)
def _cleanup():
    """Remove gate artifacts before and after each test."""
    _remove_artifacts()
    yield
    _remove_artifacts()


def _remove_artifacts():
    if os.path.isdir(GATE_DIR):
        shutil.rmtree(GATE_DIR)
    for f in ["results.json", "lap_summary.json", "grid.json", "leaderboard.json"]:
        p = os.path.join(REPO_ROOT, f)
        if os.path.isfile(p):
            os.remove(p)


@pytest.mark.smoke
def test_init_creates_project():
    """npcrace init creates a car project directory with required files."""
    result = _run(["init", GATE_CAR])
    assert result.returncode == 0, f"init failed: {result.stderr}"
    assert os.path.isdir(GATE_DIR)
    assert os.path.isfile(os.path.join(GATE_DIR, "car.py"))
    assert os.path.isfile(os.path.join(GATE_DIR, "gearbox.py"))
    assert os.path.isfile(os.path.join(GATE_DIR, "cooling.py"))
    assert os.path.isfile(os.path.join(GATE_DIR, "strategy.py"))


@pytest.mark.smoke
def test_validate_passes():
    """npcrace validate passes on freshly initialized project."""
    _run(["init", GATE_CAR])
    result = _run(["validate", os.path.join(GATE_DIR, "car.py")])
    assert result.returncode == 0, f"validate failed: {result.stderr}"
    assert "PASS" in result.stdout


@pytest.mark.smoke
def test_race_produces_results():
    """npcrace run produces results.json with timing data."""
    _run(["init", GATE_CAR])
    result = _run(["run", "--car-dir", CARS_DIR, "--track", "monza", "--laps", "1"])
    assert result.returncode == 0, f"race failed: {result.stderr}"

    results_path = os.path.join(REPO_ROOT, "results.json")
    assert os.path.isfile(results_path), "results.json not created"

    with open(results_path) as f:
        data = json.load(f)
    # results.json is a dict with "cars" key
    cars = data.get("cars", data) if isinstance(data, dict) else data
    assert len(cars) > 0
    names = [c.get("name", "") for c in cars]
    assert any("zzz" in n.lower() or "gate" in n.lower() for n in names), (
        f"Gate car not in results. Cars: {names}"
    )


@pytest.mark.smoke
def test_gearbox_edit_changes_lap_time():
    """Editing gearbox shift point produces a different lap time."""
    _run(["init", GATE_CAR])

    # Race 1: default gearbox
    _run(["run", "--car-dir", CARS_DIR, "--track", "monza", "--laps", "1"])
    with open(os.path.join(REPO_ROOT, "results.json")) as f:
        results_1 = json.load(f)

    cars_1 = results_1.get("cars", results_1) if isinstance(results_1, dict) else results_1
    gate_1 = [r for r in cars_1 if "zzz" in r.get("name", "").lower()]
    assert gate_1, f"Gate car missing from race 1: {[r.get('name') for r in cars_1]}"
    time_1 = gate_1[0]["total_time_s"]

    # Edit gearbox: shift earlier
    gearbox_path = os.path.join(GATE_DIR, "gearbox.py")
    with open(gearbox_path, "w") as f:
        f.write(
            'def gearbox(rpm, speed, current_gear, throttle):\n'
            '    if rpm > 11000 and current_gear < 8:\n'
            '        return current_gear + 1\n'
            '    if rpm < 5000 and current_gear > 1:\n'
            '        return current_gear - 1\n'
            '    return current_gear\n'
        )

    # Race 2: modified gearbox
    os.remove(os.path.join(REPO_ROOT, "results.json"))
    _run(["run", "--car-dir", CARS_DIR, "--track", "monza", "--laps", "1"])
    with open(os.path.join(REPO_ROOT, "results.json")) as f:
        results_2 = json.load(f)

    cars_2 = results_2.get("cars", results_2) if isinstance(results_2, dict) else results_2
    gate_2 = [r for r in cars_2 if "zzz" in r.get("name", "").lower()]
    assert gate_2, f"Gate car missing from race 2: {[r.get('name') for r in cars_2]}"
    time_2 = gate_2[0]["total_time_s"]

    assert time_1 != time_2, (
        f"Lap time unchanged after gearbox edit: {time_1:.3f}s both times"
    )


@pytest.mark.smoke
def test_submit_and_leaderboard():
    """npcrace submit + leaderboard --add work on race results."""
    _run(["init", GATE_CAR])
    _run(["run", "--car-dir", CARS_DIR, "--track", "monza", "--laps", "1"])

    results_path = os.path.join(REPO_ROOT, "results.json")
    assert os.path.isfile(results_path)

    # Submit
    result = _run(["submit", results_path])
    assert result.returncode == 0, f"submit failed: {result.stderr}"

    # Leaderboard add
    lb_path = os.path.join(REPO_ROOT, "leaderboard.json")
    result = _run(["leaderboard", "--add", results_path, "--file", lb_path])
    assert result.returncode == 0, f"leaderboard failed: {result.stderr}"
    assert os.path.isfile(lb_path), "leaderboard.json not created"
