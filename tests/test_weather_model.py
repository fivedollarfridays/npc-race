"""Tests for engine.weather_model — weather state machine + grip/wear penalties."""

import random

from engine.weather_model import (
    DRY,
    DRY_COMPOUNDS,
    create_weather_state,
    update_weather,
    get_wetness_grip_mult,
    get_wetness_wear_mult,
    generate_forecast,
    get_optimal_compound,
)


# ── State creation ──────────────────────────────────────────────


class TestCreateWeatherState:
    def test_initial_state_dry(self):
        ws = create_weather_state()
        assert ws["state"] == DRY
        assert ws["wetness"] == 0.0
        assert "lap_count" in ws


# ── State transitions ──────────────────────────────────────────


class TestUpdateWeather:
    def test_update_can_transition(self):
        """Run 100 updates from dry; at least one should go to damp."""
        rng = random.Random(42)
        transitioned = False
        for _ in range(100):
            ws = create_weather_state()
            ws = update_weather(ws, rng)
            if ws["state"] != DRY:
                transitioned = True
                break
        assert transitioned, "Expected at least one transition in 100 tries"

    def test_dry_stays_mostly_dry(self):
        """10 updates from dry — most should stay dry (92% chance each)."""
        rng = random.Random(123)
        dry_count = 0
        for _ in range(10):
            ws = create_weather_state()
            ws = update_weather(ws, rng)
            if ws["state"] == DRY:
                dry_count += 1
        assert dry_count >= 7, f"Expected mostly dry, got {dry_count}/10"


# ── Grip multiplier ────────────────────────────────────────────


class TestWetnessGripMult:
    def test_wetness_grip_dry_tires_on_dry(self):
        mult = get_wetness_grip_mult(0.0, "soft")
        assert abs(mult - 1.0) < 0.01

    def test_wetness_grip_dry_tires_on_wet(self):
        mult = get_wetness_grip_mult(0.5, "soft")
        assert abs(mult - 0.7) < 0.01

    def test_wetness_grip_dry_tires_catastrophic(self):
        mult = get_wetness_grip_mult(1.0, "soft")
        assert abs(mult - 0.4) < 0.01

    def test_wetness_grip_intermediate_optimal(self):
        mult = get_wetness_grip_mult(0.45, "intermediate")
        assert mult > 0.95, f"Expected near 1.0 at optimal, got {mult}"

    def test_wetness_grip_intermediate_on_dry(self):
        mult = get_wetness_grip_mult(0.0, "intermediate")
        assert mult < 0.7, f"Expected < 0.7 on dry, got {mult}"

    def test_wetness_grip_wet_optimal(self):
        mult = get_wetness_grip_mult(0.8, "wet")
        assert mult > 0.75, f"Expected near 1.0 at optimal, got {mult}"

    def test_wetness_grip_wet_on_dry(self):
        mult = get_wetness_grip_mult(0.0, "wet")
        assert mult < 0.5, f"Expected < 0.5 on dry, got {mult}"


# ── Wear multiplier ────────────────────────────────────────────


class TestWetnessWearMult:
    def test_wetness_wear_dry_on_wet(self):
        mult = get_wetness_wear_mult(0.5, "soft")
        assert mult > 1.0, f"Expected > 1.0 for dry compound on wet, got {mult}"

    def test_wetness_wear_correct_compound(self):
        # Dry compound on dry track — normal wear
        mult = get_wetness_wear_mult(0.0, "medium")
        assert abs(mult - 1.0) < 0.1, f"Expected ~1.0, got {mult}"


# ── Forecast ───────────────────────────────────────────────────


class TestForecast:
    def test_forecast_length(self):
        rng = random.Random(42)
        ws = create_weather_state()
        fc = generate_forecast(ws, 5, rng)
        assert len(fc) == 5

    def test_forecast_has_noise(self):
        """Forecast shouldn't exactly match actual future wetness."""
        rng = random.Random(42)
        ws = create_weather_state()
        fc = generate_forecast(ws, 5, rng)
        # All entries are (lap, predicted_wetness) tuples
        for lap, predicted in fc:
            assert isinstance(lap, int)
            assert isinstance(predicted, float)


# ── Optimal compound ───────────────────────────────────────────


class TestOptimalCompound:
    def test_optimal_compound_dry(self):
        c = get_optimal_compound(0.0)
        assert c in DRY_COMPOUNDS, f"Expected dry compound, got {c}"

    def test_optimal_compound_damp(self):
        c = get_optimal_compound(0.4)
        assert c == "intermediate"

    def test_optimal_compound_wet(self):
        c = get_optimal_compound(0.8)
        assert c == "wet"
