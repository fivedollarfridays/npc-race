"""Tests for engine/damage.py — car damage model."""

from engine.damage import (
    create_damage_state,
    apply_damage,
    compute_damage_penalties,
    repair_in_pit,
    DNF_THRESHOLD,
    PIT_REPAIR_EXTRA_TICKS,
)


class TestCreateDamageState:
    def test_initial_damage_zero(self):
        state = create_damage_state()
        assert state["damage"] == 0.0
        assert state["dnf"] is False


class TestApplyDamage:
    def test_apply_damage_increases(self):
        state = create_damage_state()
        state = apply_damage(state, 0.1)
        state = apply_damage(state, 0.1)
        assert abs(state["damage"] - 0.2) < 1e-9

    def test_apply_damage_capped_at_max(self):
        state = create_damage_state()
        state = apply_damage(state, 2.0)
        assert state["damage"] == 1.0

    def test_dnf_triggered_above_threshold(self):
        state = create_damage_state()
        state = apply_damage(state, 0.85)
        assert state["dnf"] is True
        assert state["damage"] >= DNF_THRESHOLD

    def test_dnf_not_triggered_below_threshold(self):
        state = create_damage_state()
        state = apply_damage(state, 0.5)
        assert state["dnf"] is False


class TestComputeDamagePenalties:
    def test_penalties_zero_at_no_damage(self):
        p = compute_damage_penalties(0.0)
        assert p["aero_mult"] == 1.0
        assert p["grip_mult"] == 1.0
        assert p["speed_mult"] == 1.0

    def test_penalties_scale_with_damage(self):
        p = compute_damage_penalties(0.5)
        assert abs(p["aero_mult"] - 0.75) < 1e-9
        assert abs(p["grip_mult"] - 0.85) < 1e-9
        assert abs(p["speed_mult"] - 0.925) < 1e-9

    def test_penalties_max_at_full_damage(self):
        p = compute_damage_penalties(1.0)
        assert abs(p["aero_mult"] - 0.5) < 1e-9


class TestRepairInPit:
    def test_pit_repair_reduces_damage(self):
        state = {"damage": 0.5, "dnf": False}
        new_state, _ = repair_in_pit(state)
        assert abs(new_state["damage"] - 0.2) < 1e-9

    def test_pit_repair_returns_extra_ticks(self):
        state = {"damage": 0.3, "dnf": False}
        _, extra = repair_in_pit(state)
        assert extra == PIT_REPAIR_EXTRA_TICKS

    def test_pit_repair_no_extra_for_undamaged(self):
        state = {"damage": 0.02, "dnf": False}
        _, extra = repair_in_pit(state)
        assert extra == 0
