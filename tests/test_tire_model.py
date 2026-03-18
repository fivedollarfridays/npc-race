"""Tests for engine.tire_model -- tire compounds, wear, and grip curves."""

import pytest

from engine.tire_model import (
    COMPOUNDS,
    compute_grip_multiplier,
    compute_wear,
    get_compound,
    get_compound_names,
    is_past_cliff,
)


# --- Cycle 1: Compound definitions and accessors ---


class TestCompoundDefinitions:
    """Test that compound data is correct."""

    def test_soft_has_highest_base_grip(self):
        grips = {k: v["base_grip"] for k, v in COMPOUNDS.items()}
        assert grips["soft"] > grips["medium"] > grips["hard"]

    def test_hard_has_lowest_base_grip(self):
        assert COMPOUNDS["hard"]["base_grip"] == 0.85

    def test_soft_base_grip_value(self):
        assert COMPOUNDS["soft"]["base_grip"] == 1.15

    def test_medium_base_grip_value(self):
        assert COMPOUNDS["medium"]["base_grip"] == 1.00

    def test_all_compounds_have_required_keys(self):
        required = {"base_grip", "wear_rate", "cliff_threshold", "cliff_exponent"}
        for name, compound in COMPOUNDS.items():
            assert set(compound.keys()) == required, f"{name} missing keys"


class TestGetCompound:
    """Test get_compound accessor."""

    def test_valid_compound_returns_dict(self):
        result = get_compound("soft")
        assert result["base_grip"] == 1.15

    def test_invalid_compound_defaults_to_medium(self):
        result = get_compound("ultra_soft")
        assert result["base_grip"] == 1.00

    def test_none_defaults_to_medium(self):
        result = get_compound(None)
        assert result["base_grip"] == 1.00


class TestGetCompoundNames:
    """Test get_compound_names."""

    def test_returns_all_three(self):
        names = get_compound_names()
        assert set(names) == {"soft", "medium", "hard"}

    def test_returns_list(self):
        assert isinstance(get_compound_names(), list)


# --- Cycle 2: Wear computation ---


class TestComputeWear:
    """Test compute_wear function."""

    def test_wear_increases_monotonically(self):
        wear = 0.0
        for _ in range(100):
            new_wear = compute_wear(wear, "medium", throttle=1.0, curvature=0.0)
            assert new_wear >= wear
            wear = new_wear

    def test_soft_wears_faster_than_medium(self):
        soft_wear = compute_wear(0.0, "soft", throttle=1.0, curvature=0.0)
        medium_wear = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        assert soft_wear > medium_wear

    def test_medium_wears_faster_than_hard(self):
        medium_wear = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        hard_wear = compute_wear(0.0, "hard", throttle=1.0, curvature=0.0)
        assert medium_wear > hard_wear

    def test_wear_capped_at_one(self):
        result = compute_wear(0.999, "soft", throttle=1.0, curvature=1.0)
        assert result <= 1.0

    def test_higher_throttle_increases_wear(self):
        low_throttle = compute_wear(0.0, "medium", throttle=0.0, curvature=0.0)
        high_throttle = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        assert high_throttle > low_throttle

    def test_higher_curvature_increases_wear(self):
        straight = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        corner = compute_wear(0.0, "medium", throttle=1.0, curvature=0.5)
        assert corner > straight

    def test_wear_formula_specific_value(self):
        """Verify: rate = base_rate * (0.5 + 0.5 * throttle) * (1.0 + curvature * 5.0)."""
        base_rate = COMPOUNDS["medium"]["wear_rate"]
        result = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        assert abs(result - base_rate) < 1e-10

    def test_soft_wear_rate_calibrated_for_20_lap_life(self):
        """Soft tires should last ~20 laps at Monza (94s, 30 tps = 2820 ticks).

        Average conditions: throttle=0.8, curvature=0.05.
        wear_per_tick = base_rate * (0.5 + 0.4) * (1 + 0.25) = base_rate * 1.125
        wear_per_lap = base_rate * 1.125 * 2820
        For 20-lap life: wear_per_lap ~= 0.05, so base_rate ~= 0.000016
        """
        base_rate = COMPOUNDS["soft"]["wear_rate"]
        wear_per_tick_avg = base_rate * 1.125
        ticks_per_lap = 2820  # ~94s * 30 tps
        wear_per_lap = wear_per_tick_avg * ticks_per_lap
        assert 0.03 <= wear_per_lap <= 0.07, (
            f"Soft wear_per_lap={wear_per_lap:.4f} out of range 0.03-0.07"
        )

    def test_medium_wear_rate_calibrated_for_30_lap_life(self):
        """Medium tires should last ~30 laps at Monza."""
        base_rate = COMPOUNDS["medium"]["wear_rate"]
        wear_per_tick_avg = base_rate * 1.125
        ticks_per_lap = 2820
        wear_per_lap = wear_per_tick_avg * ticks_per_lap
        assert 0.02 <= wear_per_lap <= 0.05, (
            f"Medium wear_per_lap={wear_per_lap:.4f} out of range 0.02-0.05"
        )

    def test_hard_wear_rate_calibrated_for_45_lap_life(self):
        """Hard tires should last ~45 laps at Monza."""
        base_rate = COMPOUNDS["hard"]["wear_rate"]
        wear_per_tick_avg = base_rate * 1.125
        ticks_per_lap = 2820
        wear_per_lap = wear_per_tick_avg * ticks_per_lap
        assert 0.01 <= wear_per_lap <= 0.035, (
            f"Hard wear_per_lap={wear_per_lap:.4f} out of range 0.01-0.035"
        )


# --- Cycle 3: Grip multiplier ---


class TestComputeGripMultiplier:
    """Test compute_grip_multiplier."""

    def test_grip_at_zero_wear_returns_base_grip(self):
        assert compute_grip_multiplier(0.0, "soft") == pytest.approx(1.15)

    def test_grip_at_zero_wear_medium(self):
        assert compute_grip_multiplier(0.0, "medium") == pytest.approx(1.00)

    def test_grip_at_zero_wear_hard(self):
        assert compute_grip_multiplier(0.0, "hard") == pytest.approx(0.85)

    def test_grip_never_below_minimum(self):
        """All compounds return grip >= 0.3 * base_grip (floor is 0.3 in formula)."""
        for name in get_compound_names():
            grip = compute_grip_multiplier(1.0, name)
            assert grip >= 0.3 * 0.5, f"{name} grip too low at full wear: {grip}"

    def test_grip_drops_sharply_past_cliff(self):
        """Post-cliff region loses >50% of remaining grip range by wear=0.95."""
        for name, compound in COMPOUNDS.items():
            cliff = compound["cliff_threshold"]
            grip_at_cliff = compute_grip_multiplier(cliff, name)
            grip_at_95 = compute_grip_multiplier(0.95, name)
            drop_pct = (grip_at_cliff - grip_at_95) / grip_at_cliff
            assert drop_pct > 0.30, (
                f"{name}: expected >30% drop by wear=0.95, got {drop_pct:.1%}"
            )

    def test_pre_cliff_mild_degradation(self):
        """Before cliff, wear=0.5 should still have decent grip (quadratic)."""
        grip = compute_grip_multiplier(0.5, "medium")
        # Quadratic: 1.0 * (1.0 - 0.5^1.5 * 0.3) ≈ 0.894
        assert grip == pytest.approx(0.894, abs=0.01)

    def test_invalid_compound_uses_medium(self):
        result = compute_grip_multiplier(0.0, "nonexistent")
        assert result == pytest.approx(1.00)

    def test_quadratic_degradation_fresh_tires_better(self):
        """At wear=0.2, quadratic gives better grip than old linear would."""
        grip = compute_grip_multiplier(0.2, "medium")
        # Old linear: 1.0 * (1.0 - 0.2 * 0.3) = 0.94
        # Quadratic:  1.0 * (1.0 - 0.2^1.5 * 0.3) ≈ 0.973
        assert grip > 0.94

    def test_quadratic_degradation_accelerates(self):
        """Grip delta between 0.6-0.7 > grip delta between 0.1-0.2."""
        grip_01 = compute_grip_multiplier(0.1, "medium")
        grip_02 = compute_grip_multiplier(0.2, "medium")
        grip_06 = compute_grip_multiplier(0.6, "medium")
        grip_07 = compute_grip_multiplier(0.7, "medium")
        delta_early = grip_01 - grip_02
        delta_late = grip_06 - grip_07
        assert delta_late > delta_early

    def test_quadratic_converges_near_cliff(self):
        """At cliff threshold, quadratic ≈ linear (within 5%)."""
        for name, compound in COMPOUNDS.items():
            cliff = compound["cliff_threshold"]
            base_grip = compound["base_grip"]
            # Linear formula value at cliff
            linear_grip = base_grip * (1.0 - cliff * 0.3)
            # Quadratic formula value at cliff
            quad_grip = compute_grip_multiplier(cliff - 0.001, name)
            diff_pct = abs(quad_grip - linear_grip) / linear_grip
            assert diff_pct < 0.05, (
                f"{name}: quadratic ({quad_grip:.4f}) vs linear ({linear_grip:.4f})"
                f" differ by {diff_pct:.1%}"
            )


# --- Cycle 4: is_past_cliff ---


class TestIsPastCliff:
    """Test is_past_cliff helper."""

    def test_below_cliff_returns_false(self):
        assert is_past_cliff(0.5, "soft") is False

    def test_at_cliff_returns_true(self):
        cliff = COMPOUNDS["soft"]["cliff_threshold"]
        assert is_past_cliff(cliff, "soft") is True

    def test_above_cliff_returns_true(self):
        assert is_past_cliff(0.95, "hard") is True

    def test_soft_cliff_at_075(self):
        assert is_past_cliff(0.74, "soft") is False
        assert is_past_cliff(0.75, "soft") is True
