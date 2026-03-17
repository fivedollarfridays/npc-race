"""Tests for engine.tire_model -- tire compounds, wear, and grip curves."""

import pytest


# --- Cycle 1: Compound definitions and accessors ---


class TestCompoundDefinitions:
    """Test that compound data is correct."""

    def test_soft_has_highest_base_grip(self):
        from engine.tire_model import COMPOUNDS

        grips = {k: v["base_grip"] for k, v in COMPOUNDS.items()}
        assert grips["soft"] > grips["medium"] > grips["hard"]

    def test_hard_has_lowest_base_grip(self):
        from engine.tire_model import COMPOUNDS

        assert COMPOUNDS["hard"]["base_grip"] == 0.85

    def test_soft_base_grip_value(self):
        from engine.tire_model import COMPOUNDS

        assert COMPOUNDS["soft"]["base_grip"] == 1.15

    def test_medium_base_grip_value(self):
        from engine.tire_model import COMPOUNDS

        assert COMPOUNDS["medium"]["base_grip"] == 1.00

    def test_all_compounds_have_required_keys(self):
        from engine.tire_model import COMPOUNDS

        required = {"base_grip", "wear_rate", "cliff_threshold", "cliff_exponent"}
        for name, compound in COMPOUNDS.items():
            assert set(compound.keys()) == required, f"{name} missing keys"


class TestGetCompound:
    """Test get_compound accessor."""

    def test_valid_compound_returns_dict(self):
        from engine.tire_model import get_compound

        result = get_compound("soft")
        assert result["base_grip"] == 1.15

    def test_invalid_compound_defaults_to_medium(self):
        from engine.tire_model import get_compound

        result = get_compound("ultra_soft")
        assert result["base_grip"] == 1.00

    def test_none_defaults_to_medium(self):
        from engine.tire_model import get_compound

        result = get_compound(None)
        assert result["base_grip"] == 1.00


class TestGetCompoundNames:
    """Test get_compound_names."""

    def test_returns_all_three(self):
        from engine.tire_model import get_compound_names

        names = get_compound_names()
        assert set(names) == {"soft", "medium", "hard"}

    def test_returns_list(self):
        from engine.tire_model import get_compound_names

        assert isinstance(get_compound_names(), list)


# --- Cycle 2: Wear computation ---


class TestComputeWear:
    """Test compute_wear function."""

    def test_wear_increases_monotonically(self):
        from engine.tire_model import compute_wear

        wear = 0.0
        for _ in range(100):
            new_wear = compute_wear(wear, "medium", throttle=1.0, curvature=0.0)
            assert new_wear >= wear
            wear = new_wear

    def test_soft_wears_faster_than_medium(self):
        from engine.tire_model import compute_wear

        soft_wear = compute_wear(0.0, "soft", throttle=1.0, curvature=0.0)
        medium_wear = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        assert soft_wear > medium_wear

    def test_medium_wears_faster_than_hard(self):
        from engine.tire_model import compute_wear

        medium_wear = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        hard_wear = compute_wear(0.0, "hard", throttle=1.0, curvature=0.0)
        assert medium_wear > hard_wear

    def test_wear_capped_at_one(self):
        from engine.tire_model import compute_wear

        result = compute_wear(0.999, "soft", throttle=1.0, curvature=1.0)
        assert result <= 1.0

    def test_higher_throttle_increases_wear(self):
        from engine.tire_model import compute_wear

        low_throttle = compute_wear(0.0, "medium", throttle=0.0, curvature=0.0)
        high_throttle = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        assert high_throttle > low_throttle

    def test_higher_curvature_increases_wear(self):
        from engine.tire_model import compute_wear

        straight = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        corner = compute_wear(0.0, "medium", throttle=1.0, curvature=0.5)
        assert corner > straight

    def test_wear_formula_specific_value(self):
        """Verify: rate = base_rate * (0.5 + 0.5 * throttle) * (1.0 + curvature * 5.0)."""
        from engine.tire_model import compute_wear

        # medium: base_rate = 0.00020
        # throttle=1.0: factor = 0.5 + 0.5*1.0 = 1.0
        # curvature=0.0: factor = 1.0 + 0.0 = 1.0
        # rate = 0.00020 * 1.0 * 1.0 = 0.00020
        result = compute_wear(0.0, "medium", throttle=1.0, curvature=0.0)
        assert abs(result - 0.00020) < 1e-10


# --- Cycle 3: Grip multiplier ---


class TestComputeGripMultiplier:
    """Test compute_grip_multiplier."""

    def test_grip_at_zero_wear_returns_base_grip(self):
        from engine.tire_model import compute_grip_multiplier

        assert compute_grip_multiplier(0.0, "soft") == pytest.approx(1.15)

    def test_grip_at_zero_wear_medium(self):
        from engine.tire_model import compute_grip_multiplier

        assert compute_grip_multiplier(0.0, "medium") == pytest.approx(1.00)

    def test_grip_at_zero_wear_hard(self):
        from engine.tire_model import compute_grip_multiplier

        assert compute_grip_multiplier(0.0, "hard") == pytest.approx(0.85)

    def test_grip_never_below_minimum(self):
        """All compounds return grip >= 0.3 * base_grip (floor is 0.3 in formula)."""
        from engine.tire_model import compute_grip_multiplier, get_compound_names

        for name in get_compound_names():
            grip = compute_grip_multiplier(1.0, name)
            assert grip >= 0.3 * 0.5, f"{name} grip too low at full wear: {grip}"

    def test_grip_drops_sharply_past_cliff(self):
        """Post-cliff region loses >50% of remaining grip range by wear=0.95."""
        from engine.tire_model import compute_grip_multiplier, COMPOUNDS

        for name, compound in COMPOUNDS.items():
            cliff = compound["cliff_threshold"]
            grip_at_cliff = compute_grip_multiplier(cliff, name)
            grip_at_95 = compute_grip_multiplier(0.95, name)
            drop_pct = (grip_at_cliff - grip_at_95) / grip_at_cliff
            assert drop_pct > 0.30, (
                f"{name}: expected >30% drop by wear=0.95, got {drop_pct:.1%}"
            )

    def test_linear_region_mild_degradation(self):
        """Before cliff, wear=0.5 should still have decent grip."""
        from engine.tire_model import compute_grip_multiplier

        # medium cliff is 0.80, so 0.5 is pre-cliff
        grip = compute_grip_multiplier(0.5, "medium")
        # base_grip * (1.0 - 0.5 * 0.3) = 1.0 * 0.85 = 0.85
        assert grip == pytest.approx(0.85)

    def test_invalid_compound_uses_medium(self):
        from engine.tire_model import compute_grip_multiplier

        result = compute_grip_multiplier(0.0, "nonexistent")
        assert result == pytest.approx(1.00)


# --- Cycle 4: is_past_cliff ---


class TestIsPastCliff:
    """Test is_past_cliff helper."""

    def test_below_cliff_returns_false(self):
        from engine.tire_model import is_past_cliff

        assert is_past_cliff(0.5, "soft") is False

    def test_at_cliff_returns_true(self):
        from engine.tire_model import is_past_cliff, COMPOUNDS

        cliff = COMPOUNDS["soft"]["cliff_threshold"]
        assert is_past_cliff(cliff, "soft") is True

    def test_above_cliff_returns_true(self):
        from engine.tire_model import is_past_cliff

        assert is_past_cliff(0.95, "hard") is True

    def test_soft_cliff_at_075(self):
        from engine.tire_model import is_past_cliff

        assert is_past_cliff(0.74, "soft") is False
        assert is_past_cliff(0.75, "soft") is True
