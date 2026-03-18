"""Tests for engine.drs_system — DRS (Drag Reduction System)."""

from engine.drs_system import (
    get_drs_zones,
    is_in_drs_zone,
    drs_speed_multiplier,
    update_drs_state,
)


# --- get_drs_zones ---

def test_get_drs_zones_empty_for_track_without_zones():
    """Track dict with no drs_zones key returns []."""
    track = {"name": "TestTrack", "character": "balanced"}
    assert get_drs_zones(track) == []


def test_get_drs_zones_returns_list_for_track_with_zones():
    """Track with drs_zones returns the list."""
    zones = [(0.05, 0.18), (0.55, 0.70)]
    track = {"name": "TestTrack", "drs_zones": zones}
    assert get_drs_zones(track) == zones


# --- is_in_drs_zone ---

def test_is_in_drs_zone_true_inside_zone():
    """distance_pct=0.10 in zone (0.05, 0.18) is True."""
    zones = [(0.05, 0.18), (0.55, 0.70)]
    assert is_in_drs_zone(0.10, zones) is True


def test_is_in_drs_zone_false_outside_all_zones():
    """distance_pct=0.40 with zones [(0.05,0.18),(0.55,0.70)] is False."""
    zones = [(0.05, 0.18), (0.55, 0.70)]
    assert is_in_drs_zone(0.40, zones) is False


def test_is_in_drs_zone_empty_zones_always_false():
    """zones=[] always returns False."""
    assert is_in_drs_zone(0.50, []) is False


# --- drs_speed_multiplier ---

def test_drs_speed_multiplier_active():
    """in_zone=True, drs_active=True returns 1.05."""
    assert drs_speed_multiplier(in_zone=True, drs_active=True) == 1.05


def test_drs_speed_multiplier_in_zone_not_active():
    """in_zone=True, drs_active=False returns 1.0."""
    assert drs_speed_multiplier(in_zone=True, drs_active=False) == 1.0


def test_drs_speed_multiplier_not_in_zone():
    """in_zone=False, drs_active=False returns 1.0."""
    assert drs_speed_multiplier(in_zone=False, drs_active=False) == 1.0


# --- update_drs_state ---

def test_update_drs_activates_when_all_conditions_met():
    """requested + in_zone + gap<=1.0 + available -> (False, True)."""
    avail, active = update_drs_state(
        drs_available=True,
        drs_active=False,
        drs_requested=True,
        in_zone=True,
        gap_ahead_s=0.8,
        lap_changed=False,
    )
    assert (avail, active) == (False, True)


def test_update_drs_no_activate_outside_zone():
    """in_zone=False -> drs_active stays False."""
    avail, active = update_drs_state(
        drs_available=True,
        drs_active=False,
        drs_requested=True,
        in_zone=False,
        gap_ahead_s=0.5,
        lap_changed=False,
    )
    assert active is False


def test_update_drs_no_activate_gap_too_large():
    """gap_ahead_s=2.0 -> drs_active stays False."""
    avail, active = update_drs_state(
        drs_available=True,
        drs_active=False,
        drs_requested=True,
        in_zone=True,
        gap_ahead_s=2.0,
        lap_changed=False,
    )
    assert active is False


def test_update_drs_no_activate_not_available():
    """drs_available=False -> drs_active stays False."""
    avail, active = update_drs_state(
        drs_available=False,
        drs_active=False,
        drs_requested=True,
        in_zone=True,
        gap_ahead_s=0.5,
        lap_changed=False,
    )
    assert active is False


def test_update_drs_deactivates_leaving_zone():
    """drs_active=True, in_zone=False -> drs_active=False."""
    avail, active = update_drs_state(
        drs_available=False,
        drs_active=True,
        drs_requested=False,
        in_zone=False,
        gap_ahead_s=0.5,
        lap_changed=False,
    )
    assert active is False


def test_update_drs_resets_on_lap_change():
    """lap_changed=True -> (True, False) regardless of prior state."""
    avail, active = update_drs_state(
        drs_available=False,
        drs_active=True,
        drs_requested=True,
        in_zone=True,
        gap_ahead_s=0.5,
        lap_changed=True,
    )
    assert (avail, active) == (True, False)


def test_monza_has_drs_zones():
    """Monza track has non-empty drs_zones."""
    from tracks import get_track

    monza = get_track("monza")
    zones = get_drs_zones(monza)
    assert len(zones) > 0
