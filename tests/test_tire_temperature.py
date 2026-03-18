"""Tests for the tire temperature model."""

from engine.tire_temperature import (
    AMBIENT_TEMP,
    OPTIMAL_TEMP,
    TEMP_WINDOW,
    heat_generation,
    heat_dissipation,
    update_tire_temp,
    tire_temp_grip_factor,
)


# --- heat_generation tests ---


def test_heat_generation_increases_with_throttle():
    """Full throttle generates more heat than half throttle."""
    full = heat_generation(throttle=1.0, curvature=0.5, lateral=0.0, dt=1.0)
    half = heat_generation(throttle=0.5, curvature=0.5, lateral=0.0, dt=1.0)
    assert full > half


def test_heat_generation_increases_with_curvature():
    """High curvature generates more heat than zero curvature."""
    high = heat_generation(throttle=0.5, curvature=1.0, lateral=0.0, dt=1.0)
    zero = heat_generation(throttle=0.5, curvature=0.0, lateral=0.0, dt=1.0)
    assert high > zero


def test_heat_generation_zero_when_all_zero():
    """Zero inputs produce zero heat."""
    result = heat_generation(throttle=0.0, curvature=0.0, lateral=0.0, dt=1.0)
    assert result == 0.0


# --- heat_dissipation tests ---


def test_heat_dissipation_increases_with_speed():
    """Higher speed dissipates more heat."""
    fast = heat_dissipation(tire_temp=80.0, speed=200.0, dt=1.0)
    slow = heat_dissipation(tire_temp=80.0, speed=50.0, dt=1.0)
    assert fast > slow


def test_heat_dissipation_at_ambient_temp():
    """At ambient temperature with zero speed, dissipation is near zero."""
    result = heat_dissipation(tire_temp=AMBIENT_TEMP, speed=0.0, dt=1.0)
    assert abs(result) < 0.01


# --- update_tire_temp tests ---


def test_update_tire_temp_clamps_to_min():
    """Temperature never drops below AMBIENT_TEMP."""
    result = update_tire_temp(tire_temp=AMBIENT_TEMP, heat_gen=0.0, heat_diss=50.0)
    assert result == AMBIENT_TEMP


def test_update_tire_temp_clamps_to_max():
    """Temperature never exceeds 150.0."""
    result = update_tire_temp(tire_temp=140.0, heat_gen=50.0, heat_diss=0.0)
    assert result == 150.0


def test_update_tire_temp_rises_with_net_heat():
    """Positive net heat increases temperature."""
    base = 60.0
    result = update_tire_temp(tire_temp=base, heat_gen=5.0, heat_diss=2.0)
    assert result > base


# --- tire_temp_grip_factor tests ---


def test_grip_factor_at_optimal_temp():
    """Returns 1.0 at the optimal temperature for each compound."""
    for compound in ("soft", "medium", "hard"):
        factor = tire_temp_grip_factor(OPTIMAL_TEMP[compound], compound)
        assert factor == 1.0, f"{compound} at optimal should be 1.0, got {factor}"


def test_grip_factor_inside_window():
    """Returns 1.0 anywhere inside the optimal window."""
    for compound in ("soft", "medium", "hard"):
        opt = OPTIMAL_TEMP[compound]
        win = TEMP_WINDOW[compound]
        # Test at edges of window
        assert tire_temp_grip_factor(opt - win, compound) == 1.0
        assert tire_temp_grip_factor(opt + win, compound) == 1.0
        # Test at midpoint between optimal and edge
        assert tire_temp_grip_factor(opt - win / 2, compound) == 1.0
        assert tire_temp_grip_factor(opt + win / 2, compound) == 1.0


def test_grip_factor_cold_tire():
    """Below the window low edge, grip is less than 1.0; at AMBIENT_TEMP it is ~0.5."""
    for compound in ("soft", "medium", "hard"):
        opt = OPTIMAL_TEMP[compound]
        win = TEMP_WINDOW[compound]
        cold_edge = opt - win
        # Just below the window
        factor = tire_temp_grip_factor(cold_edge - 1.0, compound)
        assert factor < 1.0
        # At ambient temp
        ambient_factor = tire_temp_grip_factor(AMBIENT_TEMP, compound)
        assert abs(ambient_factor - 0.5) < 0.05, (
            f"{compound} at ambient should be ~0.5, got {ambient_factor}"
        )


def test_grip_factor_blistered_tire():
    """Above the window high edge, grip is less than 1.0; at 150 deg it is ~0.5."""
    for compound in ("soft", "medium", "hard"):
        opt = OPTIMAL_TEMP[compound]
        win = TEMP_WINDOW[compound]
        hot_edge = opt + win
        # Just above the window
        factor = tire_temp_grip_factor(hot_edge + 1.0, compound)
        assert factor < 1.0
        # At 150 degrees
        blister_factor = tire_temp_grip_factor(150.0, compound)
        assert abs(blister_factor - 0.5) < 0.05, (
            f"{compound} at 150 should be ~0.5, got {blister_factor}"
        )


def test_grip_factor_monotone_on_cold_side():
    """Grip increases as temperature rises from cold toward optimal."""
    compound = "medium"
    opt = OPTIMAL_TEMP[compound]
    win = TEMP_WINDOW[compound]
    cold_edge = opt - win
    temps = [AMBIENT_TEMP, (AMBIENT_TEMP + cold_edge) / 2, cold_edge]
    factors = [tire_temp_grip_factor(t, compound) for t in temps]
    for i in range(len(factors) - 1):
        assert factors[i] < factors[i + 1] or factors[i] == factors[i + 1] == 1.0


def test_compound_specific_windows():
    """Soft optimal (90) differs from hard optimal (70)."""
    assert OPTIMAL_TEMP["soft"] != OPTIMAL_TEMP["hard"]
    assert OPTIMAL_TEMP["soft"] == 90.0
    assert OPTIMAL_TEMP["hard"] == 70.0
