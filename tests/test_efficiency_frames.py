"""T45.4 — Efficiency data in PartsRaceSim frame export."""

import pytest

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from tracks import get_track
from engine.track_gen import interpolate_track

pytestmark = pytest.mark.smoke

CARS_DIR = "cars"


def _run_short_race(laps=1, max_ticks=3000):
    """Run a 1-lap race and return the sim."""
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)
    sim = PartsRaceSim(cars, pts, laps=laps, seed=42, track_name="monza",
                       real_length_m=td.get("real_length_m"))
    sim.run(max_ticks=max_ticks)
    return sim


class TestEfficiencyInFrames:
    """Efficiency fields appear in replay frame dicts."""

    def test_frame_has_efficiency_product(self):
        sim = _run_short_race()
        # Check a mid-race frame (not tick 0 where cars haven't moved)
        frame = sim.history[len(sim.history) // 2]
        car_data = frame[0]
        assert "efficiency_product" in car_data

    def test_frame_has_gearbox_efficiency(self):
        sim = _run_short_race()
        frame = sim.history[len(sim.history) // 2]
        car_data = frame[0]
        assert "gearbox_efficiency" in car_data

    def test_frame_has_cooling_efficiency(self):
        sim = _run_short_race()
        frame = sim.history[len(sim.history) // 2]
        car_data = frame[0]
        assert "cooling_efficiency" in car_data

    def test_efficiency_product_in_range(self):
        sim = _run_short_race()
        for frame in sim.history[10:]:
            for car_data in frame:
                ep = car_data["efficiency_product"]
                assert 0.0 <= ep <= 1.0, f"efficiency_product {ep} out of range"

    def test_individual_efficiencies_in_range(self):
        sim = _run_short_race()
        for frame in sim.history[10:]:
            for car_data in frame:
                gb = car_data["gearbox_efficiency"]
                cool = car_data["cooling_efficiency"]
                assert 0.0 <= gb <= 1.0, f"gearbox_efficiency {gb} out of range"
                assert 0.0 <= cool <= 1.0, f"cooling_efficiency {cool} out of range"

    def test_efficiency_varies_across_ticks(self):
        """Efficiency should not be constant — it changes with conditions."""
        sim = _run_short_race()
        products = [sim.history[i][0]["efficiency_product"]
                    for i in range(10, min(200, len(sim.history)))]
        # There should be some variation (not all identical)
        assert len(set(products)) > 1, "efficiency_product is constant across all ticks"
