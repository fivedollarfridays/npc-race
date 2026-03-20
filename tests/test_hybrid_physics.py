"""Tests for hybrid physics — ERS, differential, and tire load/grip."""

from engine.hybrid_physics import (
    ERS_DEPLOY_LIMIT_MJ_PER_LAP,
    ERS_HARVEST_LIMIT_MJ_PER_LAP,
    create_ers_state,
    update_ers,
    reset_ers_lap,
    compute_diff_effect,
    compute_diff_tire_wear,
    compute_tire_load,
    compute_grip_from_load,
)


# ---------------------------------------------------------------------------
# ERS tests
# ---------------------------------------------------------------------------

class TestERSDeploy:
    def test_ers_deploy_drains_battery(self):
        """Deploying reduces energy."""
        ers = create_ers_state()
        initial_energy = ers["energy_mj"]
        updated, actual_kw = update_ers(ers, deploy_kw=120, harvest_kw=0, dt=1.0)
        assert updated["energy_mj"] < initial_energy
        assert actual_kw > 0

    def test_ers_deploy_limited_per_lap(self):
        """Can't deploy more than 4 MJ per lap."""
        ers = create_ers_state()
        # Try to deploy a huge amount in one step
        updated, _ = update_ers(ers, deploy_kw=120, harvest_kw=0, dt=100.0)
        assert updated["lap_deploy_mj"] <= ERS_DEPLOY_LIMIT_MJ_PER_LAP


class TestERSHarvest:
    def test_ers_harvest_charges_battery(self):
        """Harvesting increases energy."""
        ers = create_ers_state()
        # Drain some first
        ers["energy_mj"] = 1.0
        updated, _ = update_ers(ers, deploy_kw=0, harvest_kw=120, dt=1.0)
        assert updated["energy_mj"] > 1.0

    def test_ers_harvest_limited_per_lap(self):
        """Can't harvest more than 2 MJ per lap."""
        ers = create_ers_state()
        ers["energy_mj"] = 0.0
        updated, _ = update_ers(ers, deploy_kw=0, harvest_kw=120, dt=100.0)
        assert updated["lap_harvest_mj"] <= ERS_HARVEST_LIMIT_MJ_PER_LAP


class TestERSTemp:
    def test_battery_temp_rises_with_use(self):
        """Heavy use increases battery temperature."""
        ers = create_ers_state()
        initial_temp = ers["battery_temp"]
        updated, _ = update_ers(ers, deploy_kw=120, harvest_kw=0, dt=1.0)
        assert updated["battery_temp"] > initial_temp


class TestERSLapReset:
    def test_reset_clears_lap_counters(self):
        """Reset per-lap counters preserves energy and temp."""
        ers = create_ers_state()
        ers["lap_deploy_mj"] = 2.0
        ers["lap_harvest_mj"] = 1.5
        ers["energy_mj"] = 2.5
        ers["battery_temp"] = 40.0
        reset = reset_ers_lap(ers)
        assert reset["lap_deploy_mj"] == 0
        assert reset["lap_harvest_mj"] == 0
        assert reset["energy_mj"] == 2.5
        assert reset["battery_temp"] == 40.0


# ---------------------------------------------------------------------------
# Differential tests
# ---------------------------------------------------------------------------

class TestDifferential:
    def test_diff_high_lock_more_traction(self):
        """Lock=100 produces more traction than lock=0."""
        trac_high, _ = compute_diff_effect(100, lateral_g=0.5, speed_kmh=200)
        trac_low, _ = compute_diff_effect(0, lateral_g=0.5, speed_kmh=200)
        assert trac_high > trac_low

    def test_diff_high_lock_more_understeer(self):
        """Lock=100 produces more understeer than lock=0 in corners."""
        _, us_high = compute_diff_effect(100, lateral_g=1.5, speed_kmh=200)
        _, us_low = compute_diff_effect(0, lateral_g=1.5, speed_kmh=200)
        assert us_high > us_low

    def test_diff_tire_wear_increases_with_lock(self):
        """Higher lock in corners wears tires more."""
        wear_high = compute_diff_tire_wear(100, lateral_g=1.0, dt=1.0)
        wear_low = compute_diff_tire_wear(0, lateral_g=1.0, dt=1.0)
        assert wear_high > wear_low


# ---------------------------------------------------------------------------
# Tire load/grip tests
# ---------------------------------------------------------------------------

class TestTireLoad:
    def test_grip_from_load_sublinear(self):
        """Doubling load doesn't double grip (load sensitivity)."""
        grip_1 = compute_grip_from_load(8000, tire_grip_base=1.0)
        grip_2 = compute_grip_from_load(16000, tire_grip_base=1.0)
        # Sublinear: doubling load should give less than 2x grip
        assert grip_2 < grip_1 * 2.0
        # But still more grip
        assert grip_2 > grip_1

    def test_tire_load_includes_downforce(self):
        """Load increases with downforce."""
        load_no_df = compute_tire_load(798, downforce_n=0, lateral_g=0)
        load_with_df = compute_tire_load(798, downforce_n=5000, lateral_g=0)
        assert load_with_df > load_no_df
