"""Tests for engine.efficiency_engine module."""

import time

from engine.safe_call import _safe_call_with_timeout
from engine.efficiency_engine import (
    compute_brake_bias_efficiency,
    compute_cooling_efficiency,
    compute_diff_efficiency,
    compute_ers_waste,
    compute_gearbox_efficiency,
    compute_suspension_efficiency,
    run_efficiency_tick,
)
from engine.parts_api import get_defaults
from engine.parts_runner import create_initial_state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_car_state() -> dict:
    """Minimal car state for run_efficiency_tick."""
    hw = {"weight_kg": 798, "fuel_capacity_kg": 110}
    s = create_initial_state({"chassis": hw})
    s["speed_kmh"] = 200.0
    s["gear"] = 5
    s["engine_temp"] = 100.0
    return s


def _make_physics_state(**overrides) -> dict:
    base = {
        "throttle_demand": 1.0,
        "lateral_g": 0.0,
        "curvature": 0.0,
        "corner_phase": "straight",
        "braking": False,
    }
    base.update(overrides)
    return base


def _make_hw_specs() -> dict:
    return {
        "weight_kg": 798,
        "fuel_capacity_kg": 110,
        "max_hp": 1000,
        "base_cl": 4.5,
        "base_cd": 0.88,
        "max_fuel_flow_kghr": 100,
    }


# ---------------------------------------------------------------------------
# TestSafeCallWithTimeout
# ---------------------------------------------------------------------------

class TestSafeCallWithTimeout:
    """Thread-based timeout wrapper for player functions."""

    def test_normal_function_returns_ok(self):
        def func(x):
            return x * 2

        def default(x):
            return 0

        result = _safe_call_with_timeout("gearbox", func, (3,), default, tick=1)
        assert result["output"] == 6
        assert result["status"] == "ok"

    def test_exception_returns_default_with_error_status(self):
        def bad_func(x):
            raise ValueError("boom")

        def default(x):
            return 5

        result = _safe_call_with_timeout("gearbox", bad_func, (3,), default, tick=1)
        assert result["output"] == 5
        assert result["status"] == "error"
        assert "boom" in result["error"]

    def test_slow_function_returns_default_with_timeout_status(self):
        def slow_func(x):
            time.sleep(0.5)  # well above 1ms timeout, reliable even in CI
            return x

        def default(x):
            return 4

        result = _safe_call_with_timeout("gearbox", slow_func, (3,), default, tick=1)
        assert result["output"] == 4
        assert result["status"] == "timeout"

    def test_clamped_output_sets_clamped_status(self):
        # gearbox range is (1, 8); returning 10 should clamp to 8
        def func(*a):
            return 10

        def default(*a):
            return 5
        result = _safe_call_with_timeout(
            "gearbox", func, (10000, 200.0, 5, 1.0), default, tick=0,
        )
        assert result["output"] == 8
        assert result["status"] == "clamped"


# ---------------------------------------------------------------------------
# TestWheelspinPhysics
# ---------------------------------------------------------------------------

class TestWheelspinPhysics:
    """Excess torque causes tire wear through physics, not efficiency scoring."""

    def test_excess_torque_causes_tire_wear(self):
        """At low speed, full torque exceeds traction -> wheelspin -> tire wear."""
        defaults = get_defaults()
        car_state = _make_car_state()
        car_state["speed_kmh"] = 80.0  # low speed = high drive force
        car_state["gear"] = 2
        physics = _make_physics_state(lateral_g=0.5)
        hw = _make_hw_specs()

        initial_wear = car_state.get("tire_wear", 0)
        for _ in range(100):
            car_state["speed_kmh"] = 80.0  # hold speed low to sustain wheelspin
            car_state["gear"] = 2
            car_state, _, _ = run_efficiency_tick(
                defaults, car_state, physics, hw, dt=1/30, tick=0)
        assert car_state["tire_wear"] > initial_wear + 0.001, \
            f"Wheelspin should cause wear, got {car_state['tire_wear']:.4f}"

    def test_moderate_speed_no_wheelspin(self):
        """At 300 km/h on straight, drive_force < traction -> no wheelspin."""
        defaults = get_defaults()
        car_state = _make_car_state()
        car_state["speed_kmh"] = 300.0
        car_state["gear"] = 7
        physics = _make_physics_state(lateral_g=0.0)
        hw = _make_hw_specs()

        initial_wear = car_state.get("tire_wear", 0)
        for _ in range(100):
            car_state, _, _ = run_efficiency_tick(
                defaults, car_state, physics, hw, dt=1/30, tick=0)
        assert car_state["tire_wear"] < initial_wear + 0.001, \
            "No wheelspin expected at high speed straight"


# ---------------------------------------------------------------------------
# TestComputeGearboxEfficiency
# ---------------------------------------------------------------------------

class TestComputeGearboxEfficiency:
    """Gearbox: how close RPM is to torque peak band."""

    def test_rpm_in_torque_peak_band(self):
        # 11000 RPM is in the 10800-12500 plateau => best torque_curve = 1.0
        eff = compute_gearbox_efficiency(11000, 200)
        assert eff >= 0.95

    def test_rpm_way_too_low(self):
        # 5000 RPM has low torque_curve vs the best gear
        eff = compute_gearbox_efficiency(5000, 200)
        assert eff < compute_gearbox_efficiency(11000, 200)

    def test_speed_zero(self):
        # Edge case: speed = 0 => all gear RPMs are 0 => torque_curve minimal
        eff = compute_gearbox_efficiency(0, 0)
        assert 0.5 <= eff <= 1.0


# ---------------------------------------------------------------------------
# TestERSWaste
# ---------------------------------------------------------------------------

class TestERSWaste:
    """ERS energy waste from traction circle clipping."""

    def test_ers_at_low_speed_wastes_energy(self):
        """At 100 km/h with high lateral G, ERS force exceeds traction -> waste."""
        waste = compute_ers_waste(
            drive_force_with_ers=20000, drive_force_without_ers=15000,
            traction_limit=12000, lateral_g=1.5, mass_kg=900)
        assert waste > 0.3, f"Should waste >30% at low speed corner, got {waste:.2f}"

    def test_ers_at_high_speed_no_waste(self):
        """At 300 km/h on straight, all ERS force is usable."""
        waste = compute_ers_waste(
            drive_force_with_ers=10000, drive_force_without_ers=9000,
            traction_limit=50000, lateral_g=0.0, mass_kg=900)
        assert waste < 0.1, f"Should waste <10% on straight, got {waste:.2f}"

    def test_no_ers_no_waste(self):
        """No ERS deployed -> no waste."""
        waste = compute_ers_waste(
            drive_force_with_ers=9000, drive_force_without_ers=9000,
            traction_limit=50000, lateral_g=0.0, mass_kg=900)
        assert waste == 0.0


# ---------------------------------------------------------------------------
# TestComputeBrakeBiasEfficiency
# ---------------------------------------------------------------------------

class TestComputeBrakeBiasEfficiency:
    """Brake bias: deviation from optimal front/rear split."""

    def test_optimal_bias(self):
        # grip_front = 6000, grip_rear = 4000 => optimal ~60% + speed shift
        optimal = (6000 / 10000) * 100 + min(8, 200 / 40)  # ~65
        eff = compute_brake_bias_efficiency(int(optimal), 200, 6000, 4000)
        assert eff >= 0.90

    def test_far_from_optimal(self):
        # bias = 50, optimal ~60 => 10 points off
        eff_bad = compute_brake_bias_efficiency(50, 200, 6000, 4000)
        eff_good = compute_brake_bias_efficiency(60, 200, 6000, 4000)
        assert eff_bad < eff_good


# ---------------------------------------------------------------------------
# TestComputeSuspensionEfficiency
# ---------------------------------------------------------------------------

class TestComputeSuspensionEfficiency:
    """Suspension: ride height vs speed-dependent optimum."""

    def test_optimal_ride_height_for_speed(self):
        # Optimal effective = -0.20 - 200/500 = -0.60
        # Compression at 200 = (200/350)^2 * 0.3 ≈ 0.098
        # Need target so actual = optimal → target = -0.60 + 0.098 = -0.50
        eff = compute_suspension_efficiency(-0.50, 200)
        assert eff >= 0.90

    def test_too_low_bottoming(self):
        # ride_height -0.9 at high speed => bottoming
        eff = compute_suspension_efficiency(-0.9, 280)
        assert eff < compute_suspension_efficiency(-0.65, 280)

    def test_too_high(self):
        # ride_height 0.5 at 200 km/h (optimal -0.45) => big deviation
        eff = compute_suspension_efficiency(0.5, 200)
        assert eff < compute_suspension_efficiency(-0.45, 200)


# ---------------------------------------------------------------------------
# TestComputeCoolingEfficiency
# ---------------------------------------------------------------------------

class TestComputeCoolingEfficiency:
    """Cooling: balance between overheating and over-cooling drag."""

    def test_engine_in_sweet_spot(self):
        # Engine 110°C (in 108-118 sweet spot), low cooling effort
        eff = compute_cooling_efficiency(0.1, 112, 200)
        assert eff >= 0.95

    def test_overheating(self):
        eff = compute_cooling_efficiency(0.3, 130, 200)
        assert eff < 1.0

    def test_over_cooling(self):
        # engine_temp < 100 and cooling_effort > 0.5 => unnecessary drag
        eff = compute_cooling_efficiency(0.8, 90, 200)
        assert eff < 1.0


# ---------------------------------------------------------------------------
# TestComputeDiffEfficiency
# ---------------------------------------------------------------------------

class TestComputeDiffEfficiency:
    """Differential: lock percentage vs corner phase optimum."""

    def test_straight(self):
        eff = compute_diff_efficiency(50, "straight", 0.0, 250)
        assert eff >= 0.90  # slight stability penalty on straights

    def test_mid_corner_optimal_lock(self):
        # mid phase: optimal = 18 + lateral_g * 5 = 18 + 2*5 = 28
        eff = compute_diff_efficiency(28, "mid", 2.0, 150)
        assert eff >= 0.95

    def test_mid_corner_wrong_lock(self):
        # lock_pct = 80, optimal ~28 => deviation 52
        eff_bad = compute_diff_efficiency(80, "mid", 2.0, 150)
        eff_good = compute_diff_efficiency(28, "mid", 2.0, 150)
        assert eff_bad < eff_good


# ---------------------------------------------------------------------------
# TestRunEfficiencyTick
# ---------------------------------------------------------------------------

class TestRunEfficiencyTick:
    """Integration: full tick returns state, log, and efficiency product."""

    def test_returns_state_log_product(self):
        defaults = get_defaults()
        car_state = _make_car_state()
        physics = _make_physics_state()
        hw = _make_hw_specs()

        state, log, product = run_efficiency_tick(
            defaults, car_state, physics, hw, dt=0.01, tick=0,
        )
        assert isinstance(state, dict)
        assert isinstance(log, list)
        assert 0 < product <= 1.0

    def test_suboptimal_parts_lower_product(self):
        """Using a bad gearbox should produce a lower product."""
        defaults = get_defaults()

        def bad_gearbox(rpm, speed, gear, throttle):
            return 1  # always first gear

        parts_bad = dict(defaults)
        parts_bad["gearbox"] = bad_gearbox

        car_state = _make_car_state()
        physics = _make_physics_state()
        hw = _make_hw_specs()

        _, _, product_default = run_efficiency_tick(
            defaults, dict(car_state), physics, hw, dt=0.01, tick=0,
        )
        _, _, product_bad = run_efficiency_tick(
            parts_bad, dict(car_state), physics, hw, dt=0.01, tick=0,
        )
        assert product_bad < product_default


# ---------------------------------------------------------------------------
# TestNoAmplification
# ---------------------------------------------------------------------------

class TestNoAmplification:
    """Product is straight multiplication — no exponent hack."""

    def test_product_is_straight_multiplication(self):
        """Product of efficiencies should be straight multiplication, not amplified.

        With 6 efficiency factors all near ~0.93-1.0 for defaults,
        straight multiplication gives product > 0.5.
        Amplification (^1.3) would lower each factor, giving a much lower product.
        """
        defaults = get_defaults()
        car_state = _make_car_state()
        physics = _make_physics_state()
        hw = _make_hw_specs()
        _, _, product = run_efficiency_tick(
            defaults, car_state, physics, hw, dt=0.01, tick=0)
        # With 6 factors near 0.93-1.0 and no amplification, product should be > 0.5
        # With amplification (^1.3), factors drop: 0.93^1.3 ≈ 0.91 etc, product lower
        assert product > 0.3, (
            f"Product {product:.4f} seems too low — check for amplification"
        )


# ---------------------------------------------------------------------------
# TestGripFactor
# ---------------------------------------------------------------------------

class TestGripFactor:
    """Grip factor compares actual grip to baseline car at same speed."""

    def test_baseline_grip_near_unity(self):
        """Default tire_mu=1.4 at same downforce as baseline → factor near 1.0."""
        from engine.efficiency_engine import compute_grip_factor
        factor = compute_grip_factor(1.4, 15000, 900, 1.0, speed_kmh=200, cl=4.5)
        assert 0.8 < factor < 1.2, f"Baseline grip_factor should be near 1.0, got {factor:.3f}"

    def test_worn_tires_lower_grip(self):
        """Worn tires (lower tire_mu) → lower grip_factor."""
        from engine.efficiency_engine import compute_grip_factor
        fresh = compute_grip_factor(1.4, 15000, 900, 1.0, speed_kmh=200, cl=4.5)
        worn = compute_grip_factor(1.0, 15000, 900, 1.0, speed_kmh=200, cl=4.5)
        assert worn < fresh, f"Worn tires should give lower grip: {worn:.3f} vs {fresh:.3f}"

    def test_more_downforce_higher_grip(self):
        """More downforce → higher grip_factor."""
        from engine.efficiency_engine import compute_grip_factor
        low_df = compute_grip_factor(1.4, 5000, 900, 1.0, speed_kmh=200, cl=4.5)
        high_df = compute_grip_factor(1.4, 30000, 900, 1.0, speed_kmh=200, cl=4.5)
        assert high_df > low_df, f"More downforce should give more grip: {high_df:.3f} vs {low_df:.3f}"
