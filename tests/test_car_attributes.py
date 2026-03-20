"""Tests for derived attributes calculator (T20.2)."""

from engine.car_attributes import compute_attributes
from engine.parts_catalog import DEFAULTS


class TestComputeAttributes:
    def test_default_build_produces_valid_attrs(self):
        attrs = compute_attributes(DEFAULTS)
        assert "top_speed_kmh" in attrs
        assert "low_speed_grip" in attrs
        assert "high_speed_grip" in attrs
        assert "braking_g" in attrs
        assert "tire_wear_mult" in attrs
        assert "fuel_kg_per_lap" in attrs
        assert "reliability" in attrs
        assert "cooling_efficiency" in attrs

    def test_high_output_engine_more_top_speed(self):
        default = compute_attributes(DEFAULTS)
        high = dict(DEFAULTS)
        high["ENGINE"] = "pu_high_output"
        fast = compute_attributes(high)
        assert fast["top_speed_kmh"] > default["top_speed_kmh"]

    def test_high_downforce_more_grip(self):
        low = dict(DEFAULTS)
        low["AERO"] = "aero_low_drag"
        high = dict(DEFAULTS)
        high["AERO"] = "aero_high_df"
        assert compute_attributes(high)["high_speed_grip"] > compute_attributes(low)["high_speed_grip"]

    def test_aggressive_brakes_higher_g(self):
        std = compute_attributes(DEFAULTS)
        agg = dict(DEFAULTS)
        agg["BRAKES"] = "brk_aggressive"
        assert compute_attributes(agg)["braking_g"] > std["braking_g"]

    def test_soft_suspension_more_mech_grip(self):
        std = compute_attributes(DEFAULTS)
        soft = dict(DEFAULTS)
        soft["SUSPENSION"] = "sus_soft"
        assert compute_attributes(soft)["low_speed_grip"] > std["low_speed_grip"]

    def test_weight_reduction_faster(self):
        std = compute_attributes(DEFAULTS)
        light = dict(DEFAULTS)
        light["WEIGHT"] = "wt_stage2"
        assert compute_attributes(light)["top_speed_kmh"] >= std["top_speed_kmh"]

    def test_attributes_in_valid_ranges(self):
        attrs = compute_attributes(DEFAULTS)
        assert 315 <= attrs["top_speed_kmh"] <= 355
        assert 0.5 <= attrs["low_speed_grip"] <= 1.5
        assert 0.5 <= attrs["high_speed_grip"] <= 1.5
        assert 4.0 <= attrs["braking_g"] <= 6.5
        assert 0.7 <= attrs["tire_wear_mult"] <= 1.5

    def test_efficient_engine_less_fuel(self):
        std = compute_attributes(DEFAULTS)
        eff = dict(DEFAULTS)
        eff["ENGINE"] = "pu_efficient"
        assert compute_attributes(eff)["fuel_kg_per_lap"] < std["fuel_kg_per_lap"]
