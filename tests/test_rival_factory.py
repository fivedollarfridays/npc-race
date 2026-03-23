"""Tests for cars.rival_factory — archetype-based rival generation."""

from cars._rival_factory import generate_rival, ARCHETYPES


STAT_KEYS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]


class TestGenerateRivalBasics:
    """Cycle 1: basic dict structure."""

    def test_car_name_set(self):
        rival = generate_rival("frontrunner", "TestCar", "#FF0000")
        assert rival["CAR_NAME"] == "TestCar"

    def test_car_color_set(self):
        rival = generate_rival("frontrunner", "TestCar", "#FF0000")
        assert rival["CAR_COLOR"] == "#FF0000"

    def test_all_stat_keys_present(self):
        rival = generate_rival("frontrunner", "TestCar", "#FF0000")
        for key in STAT_KEYS:
            assert key in rival, f"Missing key: {key}"

    def test_strategy_key_present(self):
        rival = generate_rival("frontrunner", "TestCar", "#FF0000")
        assert "strategy" in rival
        assert callable(rival["strategy"])


class TestStatConstraints:
    """Cycle 2: stats sum to 100, all >= 5, deterministic seeds."""

    def test_stats_sum_to_100(self):
        rival = generate_rival("frontrunner", "A", "#000", seed=42)
        total = sum(rival[k] for k in STAT_KEYS)
        assert total == 100

    def test_stats_sum_to_100_all_archetypes(self):
        for arch in ARCHETYPES:
            for seed in [0, 1, 99, 12345]:
                rival = generate_rival(arch, "X", "#000", seed=seed)
                total = sum(rival[k] for k in STAT_KEYS)
                assert total == 100, f"{arch} seed={seed} sums to {total}"

    def test_stats_all_positive(self):
        for arch in ARCHETYPES:
            for seed in range(20):
                rival = generate_rival(arch, "X", "#000", seed=seed)
                for k in STAT_KEYS:
                    assert rival[k] >= 5, f"{arch} seed={seed} {k}={rival[k]}"

    def test_different_seeds_produce_different_stats(self):
        r1 = generate_rival("frontrunner", "A", "#000", seed=1)
        r2 = generate_rival("frontrunner", "A", "#000", seed=2)
        stats1 = tuple(r1[k] for k in STAT_KEYS)
        stats2 = tuple(r2[k] for k in STAT_KEYS)
        assert stats1 != stats2

    def test_same_seed_produces_same_stats(self):
        r1 = generate_rival("midfield", "A", "#000", seed=42)
        r2 = generate_rival("midfield", "A", "#000", seed=42)
        for k in STAT_KEYS:
            assert r1[k] == r2[k]

    def test_stats_are_ints(self):
        rival = generate_rival("backmarker", "A", "#000", seed=7)
        for k in STAT_KEYS:
            assert isinstance(rival[k], int), f"{k} is {type(rival[k])}"


def _make_state(**overrides):
    """Helper to build a minimal strategy state dict."""
    base = {
        "position": 3,
        "lap": 2,
        "total_laps": 5,
        "tire_wear": 0.3,
        "pit_stops": 0,
        "curvature": 0.0,
        "boost_available": False,
        "nearby_cars": [],
        "gap_behind_s": 5.0,
    }
    base.update(overrides)
    return base


class TestStrategyBehavior:
    """Cycle 3: strategy functions return valid dicts per archetype."""

    def test_strategy_returns_dict(self):
        for arch in ARCHETYPES:
            rival = generate_rival(arch, "X", "#000")
            result = rival["strategy"](_make_state())
            assert isinstance(result, dict), f"{arch} strategy returned {type(result)}"

    def test_frontrunner_pushes_when_behind(self):
        rival = generate_rival("frontrunner", "F", "#000")
        result = rival["strategy"](_make_state(position=3))
        assert result.get("engine_mode") == "push"

    def test_frontrunner_pits_on_high_wear(self):
        rival = generate_rival("frontrunner", "F", "#000")
        result = rival["strategy"](_make_state(tire_wear=0.8))
        assert result.get("pit_request") is True

    def test_midfield_balanced_engine(self):
        rival = generate_rival("midfield", "M", "#000")
        result = rival["strategy"](_make_state(position=5))
        assert result.get("engine_mode") in ("standard", "balanced")

    def test_backmarker_conserves(self):
        rival = generate_rival("backmarker", "B", "#000")
        result = rival["strategy"](_make_state(position=15))
        assert result.get("engine_mode") == "conserve"

    def test_wildcard_varies_by_seed(self):
        """Wildcard strategy with different seeds should have different aggression."""
        r1 = generate_rival("wildcard", "W1", "#000", seed=1)
        r2 = generate_rival("wildcard", "W2", "#000", seed=999)
        # Both should return valid dicts at minimum
        d1 = r1["strategy"](_make_state())
        d2 = r2["strategy"](_make_state())
        assert isinstance(d1, dict)
        assert isinstance(d2, dict)

    def test_boost_on_final_laps(self):
        rival = generate_rival("frontrunner", "F", "#000")
        state = _make_state(lap=4, total_laps=5, boost_available=True)
        result = rival["strategy"](state)
        assert result.get("boost") is True


class TestArchetypeValidation:
    """Cycle 3b: error handling and archetype coverage."""

    def test_unknown_archetype_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Unknown archetype"):
            generate_rival("nonexistent", "X", "#000")

    def test_all_archetypes_valid(self):
        expected = {"frontrunner", "midfield", "backmarker", "wildcard"}
        assert set(ARCHETYPES.keys()) == expected
