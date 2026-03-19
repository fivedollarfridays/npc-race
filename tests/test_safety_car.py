"""Tests for the safety car state machine."""
import random

from engine.safety_car import (
    ACTIVE,
    DEPLOYED,
    ENDING,
    INACTIVE,
    SC_FUEL_MULT,
    SC_PACE,
    SC_PIT_TIME_REDUCTION,
    SC_TIRE_DEG_MULT,
    create_sc_state,
    get_sc_modifiers,
    get_sc_speed_limit,
    is_sc_active,
    should_compress_gaps,
    trigger_sc,
    update_sc,
)


def test_initial_state_inactive():
    """Fresh SC state should be INACTIVE with zeroed counters."""
    sc = create_sc_state()
    assert sc["status"] == INACTIVE
    assert sc["laps_remaining"] == 0
    assert sc["laps_active"] == 0
    assert sc["reason"] is None
    assert sc["deploy_tick"] is None
    assert sc["deploy_lap"] is None


def test_trigger_deploys_sc():
    """Triggering SC from INACTIVE should move to DEPLOYED."""
    sc = create_sc_state()
    rng = random.Random(42)
    sc = trigger_sc(sc, "crash", rng, tick=1000, lap=5)
    assert sc["status"] == DEPLOYED
    assert sc["reason"] == "crash"
    assert sc["deploy_tick"] == 1000
    assert sc["deploy_lap"] == 5
    assert sc["laps_active"] == 0


def test_sc_lasts_3_to_5_laps():
    """Duration should be between SC_MIN_LAPS and SC_MAX_LAPS."""
    durations = set()
    for seed in range(100):
        sc = create_sc_state()
        rng = random.Random(seed)
        sc = trigger_sc(sc, "debris", rng, tick=0, lap=1)
        durations.add(sc["laps_remaining"])
    assert all(3 <= d <= 5 for d in durations)


def test_update_deployed_to_active():
    """Update on DEPLOYED state should transition to ACTIVE."""
    sc = create_sc_state()
    rng = random.Random(42)
    sc = trigger_sc(sc, "crash", rng, tick=0, lap=1)
    assert sc["status"] == DEPLOYED
    sc = update_sc(sc, leader_lap=2)
    assert sc["status"] == ACTIVE


def test_update_active_decrements_laps():
    """Each update in ACTIVE should decrement laps_remaining."""
    sc = create_sc_state()
    rng = random.Random(0)
    sc = trigger_sc(sc, "crash", rng, tick=0, lap=1)
    sc = update_sc(sc, leader_lap=2)  # DEPLOYED -> ACTIVE
    initial_laps = sc["laps_remaining"]
    sc = update_sc(sc, leader_lap=3)  # ACTIVE update
    assert sc["laps_remaining"] == initial_laps - 1


def test_transitions_to_ending():
    """When laps_remaining reaches 1, status should become ENDING."""
    sc = create_sc_state()
    rng = random.Random(99)  # seed that gives duration 3
    sc = trigger_sc(sc, "spin", rng, tick=0, lap=1)
    sc = update_sc(sc, leader_lap=2)  # DEPLOYED -> ACTIVE
    # Keep updating until ENDING
    for lap in range(3, 20):
        sc = update_sc(sc, leader_lap=lap)
        if sc["status"] == ENDING:
            break
    assert sc["status"] == ENDING


def test_ending_to_inactive():
    """ENDING with laps_remaining 0 should go back to INACTIVE."""
    sc = create_sc_state()
    rng = random.Random(99)
    sc = trigger_sc(sc, "spin", rng, tick=0, lap=1)
    sc = update_sc(sc, leader_lap=2)  # DEPLOYED -> ACTIVE
    # Drive through all states to INACTIVE
    for lap in range(3, 30):
        sc = update_sc(sc, leader_lap=lap)
        if sc["status"] == INACTIVE:
            break
    assert sc["status"] == INACTIVE
    assert sc["reason"] is None


def test_speed_limit_when_active():
    """Speed limit should be SC_PACE when SC is active."""
    sc = create_sc_state()
    rng = random.Random(42)
    sc = trigger_sc(sc, "crash", rng, tick=0, lap=1)
    assert get_sc_speed_limit(sc) == SC_PACE
    sc = update_sc(sc, leader_lap=2)  # ACTIVE
    assert get_sc_speed_limit(sc) == SC_PACE


def test_no_speed_limit_when_inactive():
    """No speed limit when SC is inactive."""
    sc = create_sc_state()
    assert get_sc_speed_limit(sc) is None


def test_modifiers_during_sc():
    """Modifiers should reduce tire/fuel wear during SC."""
    sc = create_sc_state()
    rng = random.Random(42)
    sc = trigger_sc(sc, "crash", rng, tick=0, lap=1)
    mods = get_sc_modifiers(sc)
    assert mods["tire_deg_mult"] == SC_TIRE_DEG_MULT
    assert mods["fuel_mult"] == SC_FUEL_MULT
    assert mods["pit_time_reduction"] == SC_PIT_TIME_REDUCTION


def test_modifiers_normal_racing():
    """Modifiers should be 1.0 / 0 when SC is inactive."""
    sc = create_sc_state()
    mods = get_sc_modifiers(sc)
    assert mods["tire_deg_mult"] == 1.0
    assert mods["fuel_mult"] == 1.0
    assert mods["pit_time_reduction"] == 0


def test_gap_compression_when_active():
    """Gaps should compress when SC is ACTIVE or ENDING."""
    sc = create_sc_state()
    rng = random.Random(42)
    sc = trigger_sc(sc, "crash", rng, tick=0, lap=1)
    sc = update_sc(sc, leader_lap=2)  # ACTIVE
    assert should_compress_gaps(sc) is True


def test_no_compression_when_inactive():
    """No gap compression when SC is inactive."""
    sc = create_sc_state()
    assert should_compress_gaps(sc) is False


def test_cannot_double_trigger():
    """Triggering SC when already deployed should be a no-op."""
    sc = create_sc_state()
    rng = random.Random(42)
    sc = trigger_sc(sc, "crash", rng, tick=100, lap=3)
    original = sc.copy()
    sc2 = trigger_sc(sc, "another crash", rng, tick=200, lap=4)
    assert sc2 == original


def test_is_sc_active_true_when_deployed():
    """is_sc_active should return True when DEPLOYED."""
    sc = create_sc_state()
    rng = random.Random(42)
    sc = trigger_sc(sc, "crash", rng, tick=0, lap=1)
    assert is_sc_active(sc) is True


def test_is_sc_active_false_when_inactive():
    """is_sc_active should return False when INACTIVE."""
    sc = create_sc_state()
    assert is_sc_active(sc) is False
