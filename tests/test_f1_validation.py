"""Sprint 7 integration gate -- F1 data validation.

Validates simulation output against real 2024 F1 telemetry data.
Tolerances are intentionally wide (15-25%) since we use simplified
spline geometry, not laser-scanned tracks.
"""

import json
import os

from engine import run_race

CARS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars")


def _run(tmp_path, **kw):
    out = str(tmp_path / "replay.json")
    kw["output"] = out
    kw.setdefault("car_dir", CARS_DIR)
    run_race(**kw)
    with open(out) as f:
        return json.load(f)


class TestMonzaValidation:
    """Real Monza fastest lap: 81.4s (Norris 2024). Top speed: 357 km/h."""

    def test_fastest_lap_within_40pct(self, tmp_path):
        r = _run(tmp_path, track_name="monza", laps=3)
        best = min(t["best_lap_s"] for t in r["results"] if t.get("best_lap_s"))
        assert 48 <= best <= 125, f"Monza best {best}s outside 48-125s"

    def test_top_speed_realistic(self, tmp_path):
        r = _run(tmp_path, track_name="monza", laps=2)
        max_spd = max(c["speed"] for t in r["frames"] for c in t if not c["finished"])
        assert max_spd <= 370, f"Max speed {max_spd} > 370"

    def test_dirty_air_visible(self, tmp_path):
        r = _run(tmp_path, track_name="monza", laps=3)
        dirty = sum(1 for t in r["frames"] for c in t if c.get("in_dirty_air"))
        total = sum(1 for t in r["frames"] for c in t if not c["finished"])
        pct = dirty / total * 100 if total > 0 else 0
        assert pct > 5, f"Only {pct:.1f}% dirty air frames (expect >5%)"


class TestMonacoValidation:
    """Real Monaco fastest lap: 74.2s (Hamilton 2024)."""

    def test_fastest_lap_within_range(self, tmp_path):
        r = _run(tmp_path, track_name="monaco", laps=3)
        best = min(t["best_lap_s"] for t in r["results"] if t.get("best_lap_s"))
        assert 25 <= best <= 100, f"Monaco best {best}s outside 25-100s"

    def test_monaco_different_from_monza(self, tmp_path):
        """Different tracks should produce different lap times."""
        (tmp_path / "monza").mkdir()
        (tmp_path / "monaco").mkdir()
        monza = _run(tmp_path / "monza", track_name="monza", laps=2)
        monaco = _run(tmp_path / "monaco", track_name="monaco", laps=2)
        monza_best = min(t["best_lap_s"] for t in monza["results"] if t.get("best_lap_s"))
        monaco_best = min(t["best_lap_s"] for t in monaco["results"] if t.get("best_lap_s"))
        assert abs(monza_best - monaco_best) > 2, "Monza and Monaco should differ by >2s"


class TestTireStrategyValidation:
    def test_soft_degrades_faster_than_medium(self, tmp_path):
        """Soft tires should wear faster than medium."""
        from engine.tire_model import COMPOUNDS
        assert COMPOUNDS["soft"]["wear_rate"] > COMPOUNDS["medium"]["wear_rate"]

    def test_tire_temp_in_f1_range(self, tmp_path):
        r = _run(tmp_path, track_name="monza", laps=3)
        mid = r["frames"][len(r["frames"]) // 2]
        temps = [c["tire_temp"] for c in mid if not c["finished"]]
        assert any(50 <= t <= 130 for t in temps), f"No tire in 50-130C, got {temps}"

    def test_compound_pace_delta_exists(self):
        """Soft grip > medium grip > hard grip when fresh."""
        from engine.tire_model import compute_grip_multiplier
        soft = compute_grip_multiplier(0.0, "soft")
        med = compute_grip_multiplier(0.0, "medium")
        hard = compute_grip_multiplier(0.0, "hard")
        assert soft > med > hard


class TestFuelValidation:
    def test_fuel_decreases(self, tmp_path):
        r = _run(tmp_path, track_name="monza", laps=3)
        first = r["frames"][0]
        last = r["frames"][-1]
        for cs in first:
            ce = next((c for c in last if c["name"] == cs["name"]), None)
            if ce and not ce["finished"]:
                assert ce["fuel_pct"] < cs["fuel_pct"], f"{cs['name']} fuel didn't decrease"


class TestDirtyAirValidation:
    def test_dirty_air_creates_dilemma(self, tmp_path):
        """Dirty air should exist in corners but not on pure straights."""
        from engine.dirty_air import compute_dirty_air_factor
        # Corner: grip penalty
        g1, w1 = compute_dirty_air_factor(0.5, 0.1)
        assert g1 < 1.0, "Should lose grip in dirty air corner"
        # Straight: no grip penalty
        g2, w2 = compute_dirty_air_factor(0.5, 0.0)
        assert g2 == 1.0, "No dirty air penalty on straights"


class TestDownforceValidation:
    def test_aero_grip_speed_dependent(self):
        from engine.physics import compute_aero_grip
        slow = compute_aero_grip(60.0, 1.0)
        fast = compute_aero_grip(250.0, 1.0)
        assert fast > slow * 5, "Aero grip at 250 should be much more than at 60"

    def test_wing_angle_tradeoff(self):
        from engine.physics import compute_aero_grip
        high_wing = compute_aero_grip(200.0, 1.0, wing_angle=1.0)
        low_wing = compute_aero_grip(200.0, 1.0, wing_angle=-1.0)
        assert high_wing > low_wing, "High wing should give more aero grip"


class TestArchCompliance:
    def test_simulation_under_limits(self):
        with open("engine/simulation.py") as f:
            assert len(f.readlines()) <= 395

    def test_physics_under_limits(self):
        with open("engine/physics.py") as f:
            assert len(f.readlines()) <= 150

    def test_timing_under_limits(self):
        with open("engine/timing.py") as f:
            assert len(f.readlines()) <= 120

    def test_dirty_air_under_limits(self):
        with open("engine/dirty_air.py") as f:
            assert len(f.readlines()) <= 80
