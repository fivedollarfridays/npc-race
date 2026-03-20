"""Tests for engine/parts_api.py — 10 car part signatures + defaults."""

from engine.parts_api import (
    CAR_PARTS,
    OUTPUT_RANGES,
    HARDWARE_SPECS,
    clamp_output,
    get_defaults,
    get_hardware_spec,
)


class TestCarPartsList:
    def test_all_10_parts_defined(self):
        assert len(CAR_PARTS) == 10
        expected = {
            "engine_map", "gearbox", "ers_deploy", "ers_harvest", "brake_bias",
            "suspension", "cooling", "fuel_mix", "differential", "strategy",
        }
        assert set(CAR_PARTS) == expected


class TestDefaultsCallable:
    def test_all_defaults_callable(self):
        defaults = get_defaults()
        assert len(defaults) == 10
        for part_name in CAR_PARTS:
            assert part_name in defaults
            assert callable(defaults[part_name])


class TestDefaultEngineMap:
    def test_default_engine_map_returns_tuple(self):
        defaults = get_defaults()
        result = defaults["engine_map"](10000, 0.8, 100)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float) or isinstance(result[0], int)
        assert isinstance(result[1], float) or isinstance(result[1], int)

    def test_engine_map_passes_through_throttle(self):
        defaults = get_defaults()
        result = defaults["engine_map"](10000, 0.5, 100)
        assert result == (0.5, 0.5)


class TestDefaultGearbox:
    def test_default_gearbox_returns_int(self):
        defaults = get_defaults()
        result = defaults["gearbox"](10000, 200, 4, 0.8)
        assert isinstance(result, int)
        assert 1 <= result <= 8

    def test_upshift_at_high_rpm(self):
        defaults = get_defaults()
        result = defaults["gearbox"](13000, 200, 4, 0.8)
        assert result == 5

    def test_downshift_at_low_rpm(self):
        defaults = get_defaults()
        result = defaults["gearbox"](5000, 80, 4, 0.2)
        assert result == 3

    def test_no_upshift_past_8(self):
        defaults = get_defaults()
        result = defaults["gearbox"](13000, 300, 8, 1.0)
        assert result == 8

    def test_no_downshift_below_1(self):
        defaults = get_defaults()
        result = defaults["gearbox"](5000, 20, 1, 0.0)
        assert result == 1


class TestOutputRanges:
    def test_output_ranges_defined(self):
        # 9 parts have ranges (not strategy)
        assert len(OUTPUT_RANGES) == 9
        assert "strategy" not in OUTPUT_RANGES
        for part in CAR_PARTS:
            if part != "strategy":
                assert part in OUTPUT_RANGES


class TestHardwareSpecs:
    def test_hardware_specs_have_options(self):
        assert "AERO_SPEC" in HARDWARE_SPECS
        assert len(HARDWARE_SPECS["AERO_SPEC"]) >= 3

    def test_engine_spec_exists(self):
        assert "ENGINE_SPEC" in HARDWARE_SPECS
        spec = get_hardware_spec("ENGINE_SPEC", "v6_1000hp")
        assert spec["max_hp"] == 1000

    def test_chassis_spec_exists(self):
        assert "CHASSIS_SPEC" in HARDWARE_SPECS
        spec = get_hardware_spec("CHASSIS_SPEC", "standard")
        assert spec["weight_kg"] == 798

    def test_get_hardware_spec_missing_returns_none(self):
        result = get_hardware_spec("ENGINE_SPEC", "nonexistent")
        assert result is None

    def test_get_hardware_spec_bad_category_returns_none(self):
        result = get_hardware_spec("BOGUS", "anything")
        assert result is None


class TestClampOutput:
    def test_clamp_output_works(self):
        result = clamp_output("ers_deploy", 200)
        assert result == 120

    def test_clamp_below_minimum(self):
        result = clamp_output("ers_deploy", -50)
        assert result == 0

    def test_clamp_within_range_unchanged(self):
        result = clamp_output("ers_deploy", 80)
        assert result == 80

    def test_clamp_tuple_output(self):
        result = clamp_output("engine_map", (1.5, -0.2))
        assert result == (1.0, 0.0)

    def test_clamp_unknown_part_returns_as_is(self):
        result = clamp_output("strategy", {"pit_request": True})
        assert result == {"pit_request": True}


class TestDefaultStrategy:
    def test_default_strategy_returns_dict(self):
        defaults = get_defaults()
        result = defaults["strategy"]({"tire_wear": 0.3})
        assert isinstance(result, dict)

    def test_strategy_pit_request_on_high_wear(self):
        defaults = get_defaults()
        result = defaults["strategy"]({"tire_wear": 0.8, "pit_stops": 0})
        assert result.get("pit_request") is True

    def test_strategy_no_pit_when_already_pitted(self):
        defaults = get_defaults()
        result = defaults["strategy"]({"tire_wear": 0.8, "pit_stops": 1})
        assert result.get("pit_request") is not True


class TestDefaultERSDeploy:
    def test_ers_deploy_returns_number(self):
        defaults = get_defaults()
        result = defaults["ers_deploy"](80, 200, 5, 1.0, False)
        assert isinstance(result, (int, float))
        assert 0 <= result <= 120

    def test_ers_deploy_zero_when_braking(self):
        defaults = get_defaults()
        result = defaults["ers_deploy"](80, 200, 5, 1.0, True)
        assert result == 0


class TestDefaultERSHarvest:
    def test_ers_harvest_returns_number(self):
        defaults = get_defaults()
        result = defaults["ers_harvest"](500, 50, 40)
        assert isinstance(result, (int, float))
        assert 0 <= result <= 120

    def test_ers_harvest_zero_when_full(self):
        defaults = get_defaults()
        result = defaults["ers_harvest"](500, 96, 40)
        assert result == 0
