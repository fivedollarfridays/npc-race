"""Tests for Code Circuit personality profiler (T60.2).

Covers: conservative, aggressive, wet specialist, one-stop hero, qualifying ace,
slipstream hunter, late braker, sunday driver, clean racer, compound experimenter,
first-race graceful handling, and profile dict shape.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.personality import profile_car


# --- Helpers ---


def _race(
    position=5, grid=5, pit_stops=1, avg_tire_wear_rate=0.05,
    wet_ratio=0.0, wet_position_gain=0, overtakes=2, defends=2,
    avg_brake_temp=400.0, slipstream_pct=0.1, best_lap_s=80.0,
    avg_lap_s=82.0, compounds_used=None, dnf=False, spins=0,
    total_laps=20,
):
    return {
        "position": position, "grid": grid, "pit_stops": pit_stops,
        "avg_tire_wear_rate": avg_tire_wear_rate, "wet_ratio": wet_ratio,
        "wet_position_gain": wet_position_gain, "overtakes": overtakes,
        "defends": defends, "avg_brake_temp": avg_brake_temp,
        "slipstream_pct": slipstream_pct, "best_lap_s": best_lap_s,
        "avg_lap_s": avg_lap_s, "compounds_used": compounds_used or ["medium", "hard"],
        "dnf": dnf, "spins": spins, "total_laps": total_laps,
    }


REQUIRED_KEYS = {"traits", "variant_name", "bio"}


# --- Test: dict shape ---


class TestProfileShape:
    def test_returns_dict_with_required_keys(self):
        result = profile_car("SpeedKing", [_race()])
        assert isinstance(result, dict)
        assert REQUIRED_KEYS.issubset(result.keys())

    def test_traits_is_list_of_strings(self):
        result = profile_car("SpeedKing", [_race()])
        assert isinstance(result["traits"], list)
        for t in result["traits"]:
            assert isinstance(t, str)

    def test_variant_name_is_string(self):
        result = profile_car("SpeedKing", [_race()])
        assert isinstance(result["variant_name"], str)
        assert len(result["variant_name"]) > 0

    def test_bio_is_string(self):
        result = profile_car("SpeedKing", [_race()])
        assert isinstance(result["bio"], str)
        assert len(result["bio"]) > 0


# --- Test: first race (graceful) ---


class TestFirstRace:
    def test_empty_history_returns_valid_profile(self):
        result = profile_car("Rookie", [])
        assert REQUIRED_KEYS.issubset(result.keys())
        assert result["traits"] == []
        assert len(result["bio"]) > 0

    def test_single_race_returns_profile(self):
        result = profile_car("Rookie", [_race()])
        assert REQUIRED_KEYS.issubset(result.keys())


# --- Test: conservative tire manager ---


class TestConservativeTireManager:
    def test_low_wear_rate_detected(self):
        history = [_race(avg_tire_wear_rate=0.02) for _ in range(5)]
        result = profile_car("Saver", history)
        assert "conservative tire manager" in result["traits"]

    def test_high_wear_rate_not_detected(self):
        history = [_race(avg_tire_wear_rate=0.12) for _ in range(5)]
        result = profile_car("Burner", history)
        assert "conservative tire manager" not in result["traits"]


# --- Test: late braker ---


class TestLateBraker:
    def test_high_brake_temp_detected(self):
        history = [_race(avg_brake_temp=750.0) for _ in range(5)]
        result = profile_car("Brave", history)
        assert "late braker" in result["traits"]

    def test_normal_brake_temp_not_detected(self):
        history = [_race(avg_brake_temp=350.0) for _ in range(5)]
        result = profile_car("Normal", history)
        assert "late braker" not in result["traits"]


# --- Test: rain specialist ---


class TestRainSpecialist:
    def test_wet_gains_detected(self):
        history = [_race(wet_ratio=0.5, wet_position_gain=3) for _ in range(4)]
        result = profile_car("RainKing", history)
        assert "rain specialist" in result["traits"]

    def test_dry_only_not_detected(self):
        history = [_race(wet_ratio=0.0, wet_position_gain=0) for _ in range(5)]
        result = profile_car("Dry", history)
        assert "rain specialist" not in result["traits"]


# --- Test: one-stop hero ---


class TestOneStopHero:
    def test_single_stops_detected(self):
        history = [_race(pit_stops=1) for _ in range(5)]
        result = profile_car("Gambler", history)
        assert "one-stop hero" in result["traits"]

    def test_multi_stop_not_detected(self):
        history = [_race(pit_stops=3) for _ in range(5)]
        result = profile_car("Pitstop", history)
        assert "one-stop hero" not in result["traits"]


# --- Test: aggressive defender ---


class TestAggressiveDefender:
    def test_high_defend_ratio_detected(self):
        history = [_race(defends=8, overtakes=2) for _ in range(5)]
        result = profile_car("Wall", history)
        assert "aggressive defender" in result["traits"]

    def test_low_defends_not_detected(self):
        history = [_race(defends=1, overtakes=5) for _ in range(5)]
        result = profile_car("Passive", history)
        assert "aggressive defender" not in result["traits"]


# --- Test: slipstream hunter ---


class TestSlipstreamHunter:
    def test_high_slipstream_detected(self):
        history = [_race(slipstream_pct=0.4) for _ in range(5)]
        result = profile_car("Drafter", history)
        assert "slipstream hunter" in result["traits"]

    def test_low_slipstream_not_detected(self):
        history = [_race(slipstream_pct=0.05) for _ in range(5)]
        result = profile_car("Solo", history)
        assert "slipstream hunter" not in result["traits"]


# --- Test: qualifying ace ---


class TestQualifyingAce:
    def test_better_grid_than_finish_detected(self):
        history = [_race(grid=2, position=6) for _ in range(5)]
        result = profile_car("QualiKing", history)
        assert "qualifying ace" in result["traits"]

    def test_gains_on_sunday_not_detected(self):
        history = [_race(grid=8, position=3) for _ in range(5)]
        result = profile_car("Racer", history)
        assert "qualifying ace" not in result["traits"]


# --- Test: sunday driver ---


class TestSundayDriver:
    def test_consistent_gains_detected(self):
        history = [_race(grid=10, position=4) for _ in range(5)]
        result = profile_car("Climber", history)
        assert "sunday driver" in result["traits"]

    def test_loses_positions_not_detected(self):
        history = [_race(grid=2, position=8) for _ in range(5)]
        result = profile_car("Slider", history)
        assert "sunday driver" not in result["traits"]


# --- Test: clean racer ---


class TestCleanRacer:
    def test_no_incidents_detected(self):
        history = [_race(spins=0, dnf=False) for _ in range(5)]
        result = profile_car("Smooth", history)
        assert "clean racer" in result["traits"]

    def test_spins_and_dnf_not_detected(self):
        history = [_race(spins=2, dnf=True) for _ in range(5)]
        result = profile_car("Chaos", history)
        assert "clean racer" not in result["traits"]


# --- Test: at least 8 traits possible ---


class TestTraitCount:
    def test_at_least_8_distinct_traits_exist(self):
        """Verify the system can produce at least 8 unique traits across profiles."""
        profiles = [
            [_race(avg_tire_wear_rate=0.02) for _ in range(5)],  # conservative tire manager
            [_race(avg_brake_temp=750) for _ in range(5)],  # late braker
            [_race(wet_ratio=0.5, wet_position_gain=3) for _ in range(5)],  # rain specialist
            [_race(pit_stops=1) for _ in range(5)],  # one-stop hero
            [_race(defends=8, overtakes=2) for _ in range(5)],  # aggressive defender
            [_race(slipstream_pct=0.4) for _ in range(5)],  # slipstream hunter
            [_race(grid=2, position=8) for _ in range(5)],  # qualifying ace
            [_race(grid=10, position=3) for _ in range(5)],  # sunday driver
            [_race(spins=0, dnf=False) for _ in range(5)],  # clean racer
        ]
        all_traits: set[str] = set()
        for i, history in enumerate(profiles):
            result = profile_car(f"Car{i}", history)
            all_traits.update(result["traits"])
        assert len(all_traits) >= 8, f"Only {len(all_traits)} distinct traits: {all_traits}"


# --- Test: bio is template-based ---


class TestBioTemplates:
    def test_bio_not_empty(self):
        result = profile_car("Any", [_race()])
        assert len(result["bio"]) > 5

    def test_bio_deterministic(self):
        history = [_race(avg_tire_wear_rate=0.02) for _ in range(5)]
        r1 = profile_car("A", history)
        r2 = profile_car("A", history)
        assert r1["bio"] == r2["bio"]

    def test_different_traits_different_bios(self):
        conserv = [_race(avg_tire_wear_rate=0.02) for _ in range(5)]
        aggro = [_race(defends=8, overtakes=2, avg_brake_temp=750) for _ in range(5)]
        r1 = profile_car("A", conserv)
        r2 = profile_car("B", aggro)
        # They should have different traits, likely different bios
        if r1["traits"] != r2["traits"]:
            assert r1["bio"] != r2["bio"]
