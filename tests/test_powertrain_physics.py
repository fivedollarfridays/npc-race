"""Tests for powertrain physics — engine/gearbox/fuel computations."""


from engine.powertrain_physics import (
    IDLE_RPM,
    MAX_RPM,
    compute_acceleration,
    compute_engine_temp,
    compute_fuel_consumption,
    compute_mixture_torque_mult,
    compute_rpm,
    compute_wheel_torque,
    torque_curve,
)


class TestTorqueCurve:
    """Torque curve shape validation."""

    def test_torque_curve_peaks_mid_range(self):
        """torque_curve(10800) should exceed torque_curve(6000)."""
        assert torque_curve(10800) > torque_curve(6000)

    def test_torque_curve_plateau(self):
        """Torque should be 1.0 in the plateau zone."""
        assert torque_curve(11000) == 1.0

    def test_torque_curve_below_idle(self):
        """Below 4000 RPM, torque is minimal."""
        assert torque_curve(3000) == 0.3

    def test_torque_curve_falloff(self):
        """Above 12500, torque falls off."""
        assert torque_curve(14000) < 1.0


class TestComputeRPM:
    """RPM from speed and gear."""

    def test_rpm_from_speed(self):
        """300 km/h in 8th gear gives a reasonable mid-range RPM."""
        rpm = compute_rpm(300, 8)
        assert 5000 <= rpm <= 9000  # ~8778 with 1.30 ratio, 2.8 final

    def test_gear_affects_rpm(self):
        """Same speed, gear 4 vs gear 8 = different RPM."""
        rpm_g4 = compute_rpm(200, 4)
        rpm_g8 = compute_rpm(200, 8)
        assert rpm_g4 != rpm_g8
        # Lower gear = higher ratio = higher RPM
        assert rpm_g4 > rpm_g8

    def test_invalid_gear_returns_idle(self):
        """Gear outside 1-8 returns idle RPM."""
        assert compute_rpm(200, 0) == IDLE_RPM
        assert compute_rpm(200, 9) == IDLE_RPM

    def test_rpm_clamped_to_range(self):
        """RPM is clamped between IDLE_RPM and MAX_RPM."""
        rpm_low = compute_rpm(5, 8)
        assert rpm_low >= IDLE_RPM
        rpm_high = compute_rpm(350, 1)
        assert rpm_high <= MAX_RPM


class TestComputeWheelTorque:
    """Wheel torque from engine output."""

    def test_higher_torque_more_wheel_torque(self):
        """torque_pct=1.0 produces more wheel torque than 0.5."""
        spec = {"torque_nm": 300}
        t_full = compute_wheel_torque(1.0, 10800, 4, spec)
        t_half = compute_wheel_torque(0.5, 10800, 4, spec)
        assert t_full > t_half

    def test_invalid_gear_zero_torque(self):
        """Invalid gear returns 0 wheel torque."""
        spec = {"torque_nm": 300}
        assert compute_wheel_torque(1.0, 10000, 0, spec) == 0
        assert compute_wheel_torque(1.0, 10000, 9, spec) == 0


class TestComputeAcceleration:
    """Acceleration from wheel torque."""

    def test_positive_torque_positive_accel(self):
        """Enough wheel torque overcomes drag for positive acceleration."""
        accel = compute_acceleration(5000, 800, 200, 100)
        assert accel > 0

    def test_more_mass_less_accel(self):
        """Heavier car accelerates slower."""
        a_light = compute_acceleration(5000, 700, 200, 100)
        a_heavy = compute_acceleration(5000, 900, 200, 100)
        assert a_light > a_heavy


class TestFuelConsumption:
    """Fuel consumption with mixture effects."""

    def test_rich_mixture_more_fuel(self):
        """lambda=0.85 consumes more fuel than lambda=1.0."""
        fuel_rich = compute_fuel_consumption(1.0, 0.85, 100, 1.0)
        fuel_stoich = compute_fuel_consumption(1.0, 1.0, 100, 1.0)
        assert fuel_rich > fuel_stoich

    def test_lean_saves_fuel(self):
        """lambda=1.15 consumes less than lambda=1.0."""
        fuel_lean = compute_fuel_consumption(1.0, 1.15, 100, 1.0)
        fuel_stoich = compute_fuel_consumption(1.0, 1.0, 100, 1.0)
        assert fuel_lean < fuel_stoich

    def test_zero_flow_no_fuel(self):
        """Zero fuel flow = zero consumption."""
        assert compute_fuel_consumption(0.0, 1.0, 100, 1.0) == 0.0


class TestEngineTemp:
    """Engine temperature dynamics."""

    def test_engine_temp_rises_under_load(self):
        """Full load increases engine temperature."""
        new_temp = compute_engine_temp(90, 1.0, 12000, 0.0, 1.0)
        assert new_temp > 90

    def test_cooling_reduces_temp(self):
        """cooling_effort=1.0 with hot engine reduces temp."""
        # Start at 120C, no load, full cooling
        new_temp = compute_engine_temp(120, 0.0, 4000, 1.0, 1.0)
        assert new_temp < 120

    def test_temp_floor_at_80(self):
        """Engine temp never drops below 80C."""
        new_temp = compute_engine_temp(80, 0.0, 4000, 1.0, 10.0)
        assert new_temp >= 80


class TestMixtureTorqueMult:
    """Mixture effect on torque."""

    def test_lean_mixture_less_torque(self):
        """lambda=1.15 gives less torque multiplier than 1.0."""
        assert compute_mixture_torque_mult(1.15) < 1.0

    def test_rich_mixture_more_torque(self):
        """lambda=0.85 gives more torque multiplier than 1.0."""
        assert compute_mixture_torque_mult(0.85) > 1.0

    def test_stoich_is_unity(self):
        """lambda=1.0 gives exactly 1.0 multiplier."""
        assert compute_mixture_torque_mult(1.0) == 1.0


class TestEngineHeatRealistic:
    """Engine temp should stabilize at realistic temperatures."""

    def test_equilibrium_with_moderate_cooling(self):
        """Full load with cooling=0.5 should stabilize at 100-130C, not 400+."""
        from engine.chassis_physics import compute_cooling_effect

        temp = 90.0
        dt = 1.0 / 30
        for _ in range(3000):  # 100 seconds
            temp = compute_engine_temp(temp, 1.0, 10000, 0.5, dt)
            e_cool, _, _ = compute_cooling_effect(0.5, temp, 400, 30, dt)
            temp -= e_cool
        assert 90 < temp < 140, f"Equilibrium {temp:.0f}C is unrealistic"

    def test_overheats_without_cooling(self):
        """Zero cooling should lead to overheating (>150C)."""
        temp = 90.0
        dt = 1.0 / 30
        for _ in range(3000):
            temp = compute_engine_temp(temp, 1.0, 10000, 0.0, dt)
        assert temp > 150, f"Should overheat without cooling, got {temp:.0f}C"

    def test_high_cooling_keeps_engine_cool(self):
        """Full cooling should stabilize below 100C."""
        from engine.chassis_physics import compute_cooling_effect

        temp = 90.0
        dt = 1.0 / 30
        for _ in range(3000):
            temp = compute_engine_temp(temp, 0.8, 10000, 1.0, dt)
            e_cool, _, _ = compute_cooling_effect(1.0, temp, 400, 30, dt)
            temp -= e_cool
        assert temp < 105, f"Full cooling should keep engine cool, got {temp:.0f}C"
