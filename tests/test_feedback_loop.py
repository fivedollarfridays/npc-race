"""Feedback loop verification — edit code, see lap time change.

THE GAME'S PROMISE: player edits part code -> lap time changes.
These tests create two car configurations, run 1-lap races, and verify
that different code produces different lap times.
"""

import os
import shutil

import pytest

from engine.car_project_loader import load_car_project
from engine.parts_simulation import PartsRaceSim
from engine.track_gen import interpolate_track
from tracks import get_track

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(REPO_ROOT, "cars", "default_project")


def _make_car(
    tmp_path,
    name: str,
    gearbox_code: str | None = None,
    cooling_code: str | None = None,
    strategy_code: str | None = None,
) -> dict:
    """Create a car dict from the default template with optional overrides."""
    car_dir = str(tmp_path / name)
    shutil.copytree(TEMPLATE, car_dir)

    if gearbox_code:
        with open(os.path.join(car_dir, "gearbox.py"), "w") as f:
            f.write(gearbox_code)
    if cooling_code:
        with open(os.path.join(car_dir, "cooling.py"), "w") as f:
            f.write(cooling_code)
    if strategy_code:
        with open(os.path.join(car_dir, "strategy.py"), "w") as f:
            f.write(strategy_code)

    return load_car_project(car_dir)


def _race_and_get_time(car: dict) -> float:
    """Run a 1-lap race with a single car and return total time in seconds."""
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)

    sim = PartsRaceSim(
        cars=[car],
        track_points=pts,
        laps=1,
        seed=42,
        track_name="monza",
        real_length_m=td.get("real_length_m"),
    )
    sim.run()
    results = sim.get_results()
    return results[0]["total_time_s"]


@pytest.mark.smoke
def test_gearbox_shift_point_affects_lap_time(tmp_path):
    """Changing gearbox shift point changes lap time."""
    # Car A: default shift at 12800 RPM (over-revving past peak power)
    car_a = _make_car(tmp_path, "car_a", gearbox_code='''\
def gearbox(rpm, speed, current_gear, throttle):
    if rpm > 12800 and current_gear < 8:
        return current_gear + 1
    if rpm < 6000 and current_gear > 1:
        return current_gear - 1
    return current_gear
''')

    # Car B: shift at 11000 RPM (within torque band)
    car_b = _make_car(tmp_path, "car_b", gearbox_code='''\
def gearbox(rpm, speed, current_gear, throttle):
    if rpm > 11000 and current_gear < 8:
        return current_gear + 1
    if rpm < 5000 and current_gear > 1:
        return current_gear - 1
    return current_gear
''')

    time_a = _race_and_get_time(car_a)
    time_b = _race_and_get_time(car_b)

    assert time_a != time_b, "Gearbox change had no effect!"
    assert abs(time_a - time_b) > 0.1, (
        f"Difference too small: {abs(time_a - time_b):.3f}s"
    )


@pytest.mark.smoke
def test_cooling_effort_affects_lap_time(tmp_path):
    """Different cooling effort values produce different lap times."""
    # Car A: max cooling (lots of drag)
    car_a = _make_car(tmp_path, "car_a", cooling_code='''\
def cooling(engine_temp, brake_temp, battery_temp, speed):
    return 1.0
''')

    # Car B: minimal cooling (less drag, risk overheating)
    car_b = _make_car(tmp_path, "car_b", cooling_code='''\
def cooling(engine_temp, brake_temp, battery_temp, speed):
    return 0.1
''')

    time_a = _race_and_get_time(car_a)
    time_b = _race_and_get_time(car_b)

    assert time_a != time_b, "Cooling change had no effect!"
    assert abs(time_a - time_b) > 0.1, (
        f"Difference too small: {abs(time_a - time_b):.3f}s"
    )


@pytest.mark.smoke
@pytest.mark.xfail(
    reason="PartsRaceSim calls strategy but does not apply engine_mode "
    "to physics yet -- strategy output is logged but not acted on. "
    "See efficiency_engine.py step 15.",
    strict=True,
)
def test_strategy_engine_mode_affects_lap_time(tmp_path):
    """Push engine mode vs conserve mode produces different lap times.

    KNOWN GAP: efficiency_engine calls the strategy function and logs the
    result, but never applies engine_mode to the car state or physics.
    This test is xfail until strategy output is wired in.
    """
    # Car A: always push (more power, more wear)
    car_a = _make_car(tmp_path, "car_a", strategy_code='''\
def strategy(state):
    return {"engine_mode": "push"}
''')

    # Car B: always conserve (less power, less wear)
    car_b = _make_car(tmp_path, "car_b", strategy_code='''\
def strategy(state):
    return {"engine_mode": "conserve"}
''')

    time_a = _race_and_get_time(car_a)
    time_b = _race_and_get_time(car_b)

    assert time_a != time_b, "Strategy change had no effect!"
    assert abs(time_a - time_b) > 0.1, (
        f"Difference too small: {abs(time_a - time_b):.3f}s"
    )
