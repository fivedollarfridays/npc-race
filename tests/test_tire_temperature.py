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


def test_grip_factor_near_optimal():
    """Near optimal temperature, grip is close to 1.0."""
    for compound in ("soft", "medium", "hard"):
        opt = OPTIMAL_TEMP[compound]
        # At optimal +/- 5 degrees, grip should be > 0.95
        assert tire_temp_grip_factor(opt - 5, compound) > 0.95
        assert tire_temp_grip_factor(opt + 5, compound) > 0.95


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
    """Above optimal, grip degrades; at 150 deg it is well below 1.0."""
    for compound in ("soft", "medium", "hard"):
        opt = OPTIMAL_TEMP[compound]
        # Well above optimal, grip should be reduced
        factor = tire_temp_grip_factor(opt + 30, compound)
        assert factor < 1.0
        # At 150 degrees, grip should be at most 0.65
        blister_factor = tire_temp_grip_factor(150.0, compound)
        assert blister_factor <= 0.65, (
            f"{compound} at 150 should be <= 0.65, got {blister_factor}"
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


def test_quadratic_grip_no_flat_plateau():
    """Quadratic parabola has no flat plateau: grip < 1.0 away from optimal."""
    for compound in ("soft", "medium", "hard"):
        opt = OPTIMAL_TEMP[compound]
        # 10 degrees from optimal should NOT be exactly 1.0
        factor_below = tire_temp_grip_factor(opt - 10, compound)
        factor_above = tire_temp_grip_factor(opt + 10, compound)
        assert factor_below < 1.0, (
            f"{compound}: expected grip < 1.0 at {opt-10}C, got {factor_below}"
        )
        assert factor_above < 1.0, (
            f"{compound}: expected grip < 1.0 at {opt+10}C, got {factor_above}"
        )


def test_quadratic_grip_smooth_transition():
    """No sudden jump at old window edges; grip changes smoothly."""
    for compound in ("soft", "medium", "hard"):
        # Sample temperatures from 30 to 140 in 1-degree steps
        temps = [float(t) for t in range(30, 141)]
        factors = [tire_temp_grip_factor(t, compound) for t in temps]
        for i in range(len(factors) - 1):
            jump = abs(factors[i + 1] - factors[i])
            assert jump < 0.05, (
                f"{compound}: jump of {jump:.4f} between "
                f"{temps[i]}C and {temps[i+1]}C"
            )


def test_quadratic_grip_symmetric_around_optimal():
    """Grip at (optimal - 20) ≈ grip at (optimal + 20)."""
    for compound in ("soft", "medium", "hard"):
        opt = OPTIMAL_TEMP[compound]
        grip_below = tire_temp_grip_factor(opt - 20, compound)
        grip_above = tire_temp_grip_factor(opt + 20, compound)
        assert abs(grip_below - grip_above) < 0.05, (
            f"{compound}: asymmetric grip below={grip_below:.4f} "
            f"above={grip_above:.4f}"
        )
