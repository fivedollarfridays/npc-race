"""Tests for ERS (Energy Recovery System) model."""

from engine.ers_model import (
    ERS_CAPACITY,
    ERS_DEPLOY_RATE,
    ERS_HARVEST_LIMIT,
    ERS_HARVEST_RATE,
    ERS_SPEED_BONUS,
    create_ers_state,
    get_ers_speed_bonus,
    reset_ers_lap,
    update_ers,
)


class TestCreateErsState:
    def test_initial_state(self):
        """Energy=4.0, lap_deploy=0, lap_harvest=0."""
        state = create_ers_state()
        assert state["energy"] == ERS_CAPACITY
        assert state["lap_deploy"] == 0.0
        assert state["lap_harvest"] == 0.0


class TestUpdateErs:
    def test_deploy_drains_battery(self):
        """Attack mode reduces energy by deploy rate * dt."""
        state = create_ers_state()
        updated = update_ers(state, "attack", braking_force=0.0, dt=1.0)
        expected_energy = ERS_CAPACITY - ERS_DEPLOY_RATE["attack"]
        assert updated["energy"] == expected_energy
        assert updated["lap_deploy"] == ERS_DEPLOY_RATE["attack"]

    def test_no_deploy_when_empty(self):
        """Energy=0 means no drain occurs."""
        state = create_ers_state()
        state["energy"] = 0.0
        updated = update_ers(state, "attack", braking_force=0.0, dt=1.0)
        assert updated["energy"] == 0.0
        assert updated["lap_deploy"] == 0.0

    def test_harvest_recovers_energy(self):
        """Braking in harvest mode recovers energy."""
        state = create_ers_state()
        state["energy"] = 2.0  # start below capacity
        braking_force = 100.0
        dt = 1.0
        updated = update_ers(state, "harvest", braking_force=braking_force, dt=dt)
        expected_harvest = braking_force * ERS_HARVEST_RATE * dt
        assert updated["energy"] == 2.0 + expected_harvest
        assert updated["lap_harvest"] == expected_harvest

    def test_harvest_capped_at_limit(self):
        """Cannot harvest more than 2.0 MJ per lap."""
        state = create_ers_state()
        state["energy"] = 1.0
        state["lap_harvest"] = ERS_HARVEST_LIMIT  # already at limit
        updated = update_ers(state, "harvest", braking_force=100.0, dt=1.0)
        # No additional harvest should occur
        assert updated["energy"] == 1.0
        assert updated["lap_harvest"] == ERS_HARVEST_LIMIT

    def test_energy_capped_at_capacity(self):
        """Energy cannot exceed 4.0 MJ even with heavy harvesting."""
        state = create_ers_state()
        state["energy"] = 3.99
        state["lap_harvest"] = 0.0
        # Large braking force that would push energy above 4.0
        updated = update_ers(state, "harvest", braking_force=500.0, dt=1.0)
        assert updated["energy"] == ERS_CAPACITY
        assert updated["energy"] <= ERS_CAPACITY


class TestGetErsSpeedBonus:
    def test_attack_speed_bonus(self):
        """Attack mode gives +8 km/h when battery > 0."""
        state = create_ers_state()
        bonus = get_ers_speed_bonus(state, "attack")
        assert bonus == ERS_SPEED_BONUS["attack"]
        assert bonus == 8.0

    def test_balanced_speed_bonus(self):
        """Balanced mode gives +4 km/h when battery > 0."""
        state = create_ers_state()
        bonus = get_ers_speed_bonus(state, "balanced")
        assert bonus == ERS_SPEED_BONUS["balanced"]
        assert bonus == 4.0

    def test_harvest_no_speed_bonus(self):
        """Harvest mode gives 0 bonus."""
        state = create_ers_state()
        bonus = get_ers_speed_bonus(state, "harvest")
        assert bonus == 0.0

    def test_no_bonus_when_empty(self):
        """No speed bonus when battery is empty, even in attack mode."""
        state = create_ers_state()
        state["energy"] = 0.0
        bonus = get_ers_speed_bonus(state, "attack")
        assert bonus == 0.0


class TestResetErsLap:
    def test_lap_reset(self):
        """Reset clears per-lap deploy and harvest counters."""
        state = create_ers_state()
        state["lap_deploy"] = 2.5
        state["lap_harvest"] = 1.8
        state["energy"] = 3.0  # energy should NOT reset
        reset = reset_ers_lap(state)
        assert reset["lap_deploy"] == 0.0
        assert reset["lap_harvest"] == 0.0
        assert reset["energy"] == 3.0  # preserved
