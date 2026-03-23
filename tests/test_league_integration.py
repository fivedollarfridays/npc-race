"""Integration tests for the league system end-to-end pipeline."""

from __future__ import annotations

from engine.car_loader import load_all_cars
from engine.car_project_loader import load_car_project
from engine.league_system import (
    determine_league,
    generate_quality_report,
    validate_car_for_league,
)


class TestLeagueAutoDetection:
    """League detection from loaded cars."""

    def test_default_project_auto_detected(self):
        """default_project with gearbox+cooling+strategy -> F3 (all F3 parts)."""
        cars = load_all_cars("cars")
        project_car = next(c for c in cars if c["CAR_NAME"] == "DefaultProject")
        league = determine_league(project_car)
        assert league == "F3"

    def test_seed_cars_all_load_with_league(self):
        """All seed cars load and get a league assignment."""
        cars = load_all_cars("cars")
        assert len(cars) >= 5
        for car in cars:
            league = determine_league(car)
            assert league in ["F3", "F2", "F1", "Championship"]

    def test_single_file_cars_default_to_f3(self):
        """Single-file cars have no _loaded_parts, so they get F3."""
        cars = load_all_cars("cars")
        single_file = [c for c in cars if c["file"].endswith(".py")]
        assert len(single_file) >= 5
        # Single-file cars lack _loaded_parts -> F3
        for car in single_file:
            assert determine_league(car) == "F3"


class TestF3Validation:
    """F3 league validation and quality gates."""

    def test_f3_car_races_with_valid_parts(self, tmp_path):
        """An F3-valid car (gearbox, cooling, strategy only) validates."""
        (tmp_path / "car.py").write_text(
            'CAR_NAME = "F3Car"\nCAR_COLOR = "#00ff00"\n'
            "POWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20\n"
        )
        (tmp_path / "gearbox.py").write_text(
            "def gearbox(rpm, speed, gear, throttle):\n"
            "    if rpm > 12000 and gear < 8: return gear + 1\n"
            "    if rpm < 7000 and gear > 1: return gear - 1\n"
            "    return gear\n"
        )
        (tmp_path / "cooling.py").write_text(
            "def cooling(engine_temp, brake_temp, battery_temp, speed):\n"
            "    return 0.4\n"
        )
        (tmp_path / "strategy.py").write_text(
            'def strategy(state):\n    return {"engine_mode": "standard"}\n'
        )
        car = load_car_project(str(tmp_path))
        league = determine_league(car)
        assert league == "F3"
        result = validate_car_for_league(car, "F3")
        assert result.passed

    def test_advisory_report_for_f3(self, tmp_path):
        """F3 car gets advisory quality report that always passes."""
        (tmp_path / "car.py").write_text(
            'CAR_NAME = "F3Car"\nCAR_COLOR = "#00ff00"\n'
            "POWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20\n"
        )
        (tmp_path / "gearbox.py").write_text(
            "def gearbox(rpm, speed, gear, throttle):\n    return 3\n"
        )
        car = load_car_project(str(tmp_path))
        report = generate_quality_report(car, "F3")
        assert report.passed is True  # advisory always passes


class TestF2Validation:
    """F2 league detection and validation."""

    def test_f2_car_with_6_parts(self, tmp_path):
        """Car with 6 F2 parts is detected as F2."""
        (tmp_path / "car.py").write_text(
            'CAR_NAME = "F2Car"\nCAR_COLOR = "#0000ff"\n'
            "POWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20\n"
        )
        for part in [
            "gearbox", "cooling", "suspension", "ers_deploy", "fuel_mix", "strategy",
        ]:
            (tmp_path / f"{part}.py").write_text(
                f"def {part}(*args, **kwargs):\n    return 0\n"
            )
        car = load_car_project(str(tmp_path))
        assert determine_league(car) == "F2"


class TestEnforcedGates:
    """F1/Championship enforced quality gates."""

    def test_enforced_gate_rejects_high_cc(self, tmp_path):
        """F1 car with very complex code is rejected."""
        lines = ["def gearbox(rpm, speed, gear, throttle):\n"]
        for i in range(20):
            lines.append(f"    if rpm > {i}: pass\n")
        lines.append("    return gear\n")
        complex_code = "".join(lines)

        (tmp_path / "car.py").write_text(
            'CAR_NAME = "BadCar"\nCAR_COLOR = "#ff0000"\n'
            "POWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20\n"
        )
        (tmp_path / "gearbox.py").write_text(complex_code)
        car = load_car_project(str(tmp_path))
        report = generate_quality_report(car, "F1")
        assert report.passed is False
        assert any(
            "CC" in v or "complexity" in v.lower()
            for v in report.blocking_violations
        )


class TestRaceIntegration:
    """Full race pipeline with league system."""

    def test_mixed_league_cars_can_race(self):
        """Cars from different leagues can race together."""
        from engine import safe_call
        from engine.parts_simulation import PartsRaceSim
        from engine.track_gen import interpolate_track
        from tracks import get_track

        safe_call.TIMEOUT_ENABLED = False
        td = get_track("monza")
        pts = interpolate_track(td["control_points"], resolution=500)
        cars = load_all_cars("cars")
        sim = PartsRaceSim(
            cars, pts, laps=1, seed=42, track_name="monza",
            real_length_m=td.get("real_length_m"),
        )
        sim.run(max_ticks=6000)
        finished = sum(1 for s in sim.car_states if s.get("finish_tick"))
        assert finished >= 5  # at least the 5 seed cars finish
