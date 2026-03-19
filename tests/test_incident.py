"""Tests for engine/incident.py — spin and lockup incident model."""
import random

from engine.incident import (
    BASE_SPIN_RISK,
    LOCKUP_DURATION_TICKS,
    LOCKUP_FLAT_SPOT_WEAR,
    SPIN_RECOVERY_TICKS_MAX,
    SPIN_RECOVERY_TICKS_MIN,
    SPIN_TIRE_WEAR_PENALTY,
    check_spin,
    compute_lockup_risk,
    compute_spin_risk,
    create_lockup_event,
    create_spin_event,
)


# ---------------------------------------------------------------------------
# compute_spin_risk tests
# ---------------------------------------------------------------------------

class TestSpinRiskLow:
    def test_spin_risk_low_when_within_grip(self):
        risk = compute_spin_risk(
            grip_available=1.0, grip_demanded=0.5,
            dirty_air_factor=1.0, tire_wear=0.0, tire_age_laps=5,
        )
        assert risk < 0.001

    def test_spin_risk_increases_with_deficit(self):
        risk = compute_spin_risk(
            grip_available=1.0, grip_demanded=1.5,
            dirty_air_factor=1.0, tire_wear=0.0, tire_age_laps=5,
        )
        assert risk > BASE_SPIN_RISK * 5

    def test_spin_risk_increases_with_tire_wear(self):
        low_wear = compute_spin_risk(
            grip_available=1.0, grip_demanded=0.8,
            dirty_air_factor=1.0, tire_wear=0.1, tire_age_laps=5,
        )
        high_wear = compute_spin_risk(
            grip_available=1.0, grip_demanded=0.8,
            dirty_air_factor=1.0, tire_wear=0.8, tire_age_laps=5,
        )
        assert high_wear > low_wear

    def test_spin_risk_increases_in_dirty_air(self):
        clean = compute_spin_risk(
            grip_available=1.0, grip_demanded=0.8,
            dirty_air_factor=1.0, tire_wear=0.0, tire_age_laps=5,
        )
        dirty = compute_spin_risk(
            grip_available=1.0, grip_demanded=0.8,
            dirty_air_factor=0.92, tire_wear=0.0, tire_age_laps=5,
        )
        assert dirty > clean

    def test_spin_risk_cold_tires(self):
        cold = compute_spin_risk(
            grip_available=1.0, grip_demanded=0.8,
            dirty_air_factor=1.0, tire_wear=0.0, tire_age_laps=0,
        )
        warm = compute_spin_risk(
            grip_available=1.0, grip_demanded=0.8,
            dirty_air_factor=1.0, tire_wear=0.0, tire_age_laps=5,
        )
        assert abs(cold / warm - 2.0) < 0.01


# ---------------------------------------------------------------------------
# check_spin tests
# ---------------------------------------------------------------------------

class TestCheckSpin:
    def test_check_spin_deterministic_with_seed(self):
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        result1 = check_spin(0.5, rng1)
        result2 = check_spin(0.5, rng2)
        assert result1 == result2


# ---------------------------------------------------------------------------
# create_spin_event tests
# ---------------------------------------------------------------------------

class TestSpinEvent:
    def test_spin_event_has_recovery_ticks(self):
        rng = random.Random(42)
        event = create_spin_event(rng)
        assert SPIN_RECOVERY_TICKS_MIN <= event["recovery_ticks"] <= SPIN_RECOVERY_TICKS_MAX

    def test_spin_event_has_tire_penalty(self):
        rng = random.Random(42)
        event = create_spin_event(rng)
        assert event["tire_penalty"] == SPIN_TIRE_WEAR_PENALTY

    def test_spin_event_has_trigger_sc(self):
        rng = random.Random(42)
        event = create_spin_event(rng)
        assert isinstance(event["trigger_sc"], bool)


# ---------------------------------------------------------------------------
# lockup tests
# ---------------------------------------------------------------------------

class TestLockup:
    def test_lockup_risk_proportional_to_braking(self):
        low = compute_lockup_risk(braking_force=0.5, grip_available=1.0)
        high = compute_lockup_risk(braking_force=2.0, grip_available=1.0)
        assert high > low

    def test_lockup_event_has_flat_spot(self):
        event = create_lockup_event()
        assert event["flat_spot_wear"] == LOCKUP_FLAT_SPOT_WEAR

    def test_lockup_event_has_duration(self):
        event = create_lockup_event()
        assert event["duration_ticks"] == LOCKUP_DURATION_TICKS
