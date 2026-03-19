"""Sprint 6 integration gate -- realism verification.

End-to-end tests that verify the simulation produces F1-realistic
physics, timing, and replay data.
"""

import json
import os

from engine import run_race

CARS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars")


def _run_race(tmp_path, **kwargs):
    output = str(tmp_path / "replay.json")
    kwargs["output"] = output
    kwargs.setdefault("car_dir", CARS_DIR)
    run_race(**kwargs)
    with open(output) as f:
        return json.load(f)


class TestRealisticLapTimes:
    def test_monza_lap_time(self, tmp_path):
        """Monza P1 lap time between 55-100 seconds."""
        replay = _run_race(tmp_path, track_name="monza", laps=3)
        best_laps = [r["best_lap_s"] for r in replay["results"] if r.get("best_lap_s")]
        fastest = min(best_laps)
        assert 55 <= fastest <= 100, f"Fastest lap {fastest}s outside 55-100s range"

    def test_monaco_lap_time(self, tmp_path):
        """Monaco P1 lap time between 30-85 seconds."""
        replay = _run_race(tmp_path, track_name="monaco", laps=3)
        best_laps = [r["best_lap_s"] for r in replay["results"] if r.get("best_lap_s")]
        fastest = min(best_laps)
        assert 30 <= fastest <= 85, f"Fastest lap {fastest}s outside 30-85s range"

    def test_car_spread_under_25_pct(self, tmp_path):
        """Fastest car lap / slowest car lap < 1.25."""
        replay = _run_race(tmp_path, track_name="monza", laps=3)
        best_laps = [r["best_lap_s"] for r in replay["results"] if r.get("best_lap_s")]
        if len(best_laps) >= 2:
            ratio = max(best_laps) / min(best_laps)
            assert ratio < 1.25, f"Car spread ratio {ratio:.3f} >= 1.25"


class TestRealisticSpeeds:
    def test_no_speed_above_370(self, tmp_path):
        """No car ever exceeds 370 km/h."""
        replay = _run_race(tmp_path, track_name="monza", laps=2)
        max_speed = max(
            c["speed"] for tick in replay["frames"] for c in tick
            if not c["finished"]
        )
        assert max_speed <= 370, f"Max speed {max_speed:.0f} km/h > 370"

    def test_min_corner_speed_above_30(self, tmp_path):
        """No car drops below 30 km/h mid-race (skip first 300 frames for warmup)."""
        replay = _run_race(tmp_path, track_name="monaco", laps=2)
        mid_frames = replay["frames"][300:]
        racing_speeds = [
            c["speed"] for tick in mid_frames for c in tick
            if not c["finished"] and c["pit_status"] == "racing" and c["speed"] > 0
        ]
        if racing_speeds:
            min_speed = min(racing_speeds)
            assert min_speed >= 30, f"Min racing speed {min_speed:.0f} km/h < 30"


class TestRealisticTireWear:
    def test_tire_wear_after_3_laps(self, tmp_path):
        """After 3 laps, tire wear between 0.02-0.30."""
        replay = _run_race(tmp_path, track_name="monza", laps=3)
        last_frame = replay["frames"][-1]
        for car in last_frame:
            if car["finished"]:
                continue
            assert 0.02 <= car["tire_wear"] <= 0.30, (
                f"{car['name']} tire_wear {car['tire_wear']:.3f} outside 0.02-0.30"
            )

    def test_tire_temp_in_operating_range(self, tmp_path):
        """By lap 3, at least one car has tire temp 65-115 C."""
        replay = _run_race(tmp_path, track_name="monza", laps=3)
        mid_frame = replay["frames"][len(replay["frames"]) // 2]
        temps = [c["tire_temp"] for c in mid_frame if not c["finished"]]
        assert any(65 <= t <= 115 for t in temps), (
            f"No car in 65-115 C range, temps: {[f'{t:.1f}' for t in temps]}"
        )


class TestRealisticFuel:
    def test_fuel_decreases(self, tmp_path):
        """Fuel pct at end < fuel pct at start."""
        replay = _run_race(tmp_path, track_name="monza", laps=3)
        first = replay["frames"][0]
        last = replay["frames"][-1]
        for car_start in first:
            car_end = next((c for c in last if c["name"] == car_start["name"]), None)
            if car_end and not car_end["finished"]:
                assert car_end["fuel_pct"] < car_start["fuel_pct"], (
                    f"{car_start['name']} fuel didn't decrease"
                )


class TestTimingInReplay:
    def test_elapsed_s_in_every_frame(self, tmp_path):
        replay = _run_race(tmp_path, track_name="monza", laps=2)
        for tick in replay["frames"][:100]:
            for car in tick:
                assert "elapsed_s" in car
                assert isinstance(car["elapsed_s"], (int, float))

    def test_results_have_timing(self, tmp_path):
        replay = _run_race(tmp_path, track_name="monza", laps=2)
        for r in replay["results"]:
            assert "total_time_s" in r
            assert "best_lap_s" in r
            assert "lap_times" in r
            assert "pit_stops" in r

    def test_lap_times_count_matches_laps(self, tmp_path):
        replay = _run_race(tmp_path, track_name="monza", laps=3)
        for r in replay["results"]:
            if r["finished"]:
                assert len(r["lap_times"]) == 3, (
                    f"{r['name']} has {len(r['lap_times'])} lap times, expected 3"
                )

    def test_best_lap_is_minimum(self, tmp_path):
        replay = _run_race(tmp_path, track_name="monza", laps=3)
        for r in replay["results"]:
            if r["finished"] and r["lap_times"]:
                assert abs(r["best_lap_s"] - min(r["lap_times"])) < 0.01

    def test_sector_info_in_frames(self, tmp_path):
        replay = _run_race(tmp_path, track_name="monza", laps=2)
        for tick in replay["frames"][:100]:
            for car in tick:
                assert "current_sector" in car
                assert car["current_sector"] in (0, 1, 2)


class TestArchCompliance:
    def test_simulation_under_limits(self):
        with open("engine/simulation.py") as f:
            lines = f.readlines()
        assert len(lines) <= 350, f"simulation.py has {len(lines)} lines (limit 350)"

    def test_physics_module_under_limits(self):
        with open("engine/physics.py") as f:
            lines = f.readlines()
        assert len(lines) <= 150, f"physics.py has {len(lines)} lines (limit 150)"

    def test_timing_module_under_limits(self):
        with open("engine/timing.py") as f:
            lines = f.readlines()
        assert len(lines) <= 120, f"timing.py has {len(lines)} lines (limit 120)"
