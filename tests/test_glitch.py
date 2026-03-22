"""Tests for engine.glitch -- reliability-based glitch system."""

import random
from engine.glitch import GlitchEngine


class TestGlitchEngine:
    def test_init_default_scale(self):
        ge = GlitchEngine()
        assert ge.reliability_scale == 0.3

    def test_custom_scale(self):
        ge = GlitchEngine(reliability_scale=1.0)
        assert ge.reliability_scale == 1.0

    def test_disabled_at_scale_zero(self):
        """No glitches when scale=0.0, even with terrible reliability."""
        ge = GlitchEngine(reliability_scale=0.0)
        rng = random.Random(42)
        glitches = sum(ge.should_glitch("gearbox", 0.50, tick, rng) for tick in range(1000))
        assert glitches == 0

    def test_high_reliability_few_glitches(self):
        """At 0.95 reliability + scale=1.0, expect ~5% glitch rate."""
        ge = GlitchEngine(reliability_scale=1.0)
        rng = random.Random(42)
        glitches = sum(ge.should_glitch("gearbox", 0.95, tick, rng) for tick in range(1000))
        assert 20 < glitches < 100  # ~5% of 1000

    def test_low_reliability_many_glitches(self):
        """At 0.70 reliability + scale=1.0, expect ~30% glitch rate."""
        ge = GlitchEngine(reliability_scale=1.0)
        rng = random.Random(42)
        glitches = sum(ge.should_glitch("gearbox", 0.70, tick, rng) for tick in range(1000))
        assert 200 < glitches < 400  # ~30% of 1000


class TestGlitchState:
    def test_glitch_has_duration(self):
        ge = GlitchEngine(reliability_scale=1.0)
        duration = ge.get_glitch_duration("gearbox")
        assert duration > 0

    def test_active_glitch_blocks_new_rolls(self):
        """While a glitch is active, should_glitch returns True without rolling."""
        ge = GlitchEngine(reliability_scale=1.0)
        # Force a glitch by setting active state
        ge.set_active_glitch("gearbox", car_idx=0, duration=10)
        # Should return True (glitch active) without needing to roll
        assert ge.is_glitching("gearbox", car_idx=0) is True
        # Tick down
        ge.tick_glitches(car_idx=0)
        assert ge.is_glitching("gearbox", car_idx=0) is True  # still active (9 left)

    def test_glitch_expires(self):
        ge = GlitchEngine(reliability_scale=1.0)
        ge.set_active_glitch("gearbox", car_idx=0, duration=2)
        ge.tick_glitches(car_idx=0)  # 1 left
        ge.tick_glitches(car_idx=0)  # 0 left
        assert ge.is_glitching("gearbox", car_idx=0) is False
