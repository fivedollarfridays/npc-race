"""Tests for engine/component_api.py — Component API with 10 function signatures."""

from engine.component_api import (
    COMPONENT_FUNCTIONS,
    HARDWARE_SPECS,
    OUTPUT_RANGES,
    clamp_output,
    get_defaults,
    get_hardware_spec,
)


class TestComponentsDefined:
    """Test all 10 components are defined."""

    def test_all_10_components_defined(self):
        assert len(COMPONENT_FUNCTIONS) == 10
        expected = [
            "engine_map", "gearbox", "ers_deploy", "ers_harvest",
            "brake_bias", "suspension", "cooling", "fuel_mix",
            "differential", "strategy",
        ]
        assert COMPONENT_FUNCTIONS == expected


class TestDefaultsCallable:
    """Test all defaults are callable."""

    def test_all_defaults_callable(self):
        defaults = get_defaults()
        assert len(defaults) == 10
        for name in COMPONENT_FUNCTIONS:
            assert callable(defaults[name]), f"{name} default not callable"


class TestDefaultEngineMap:
    """Test default_engine_map returns a tuple of two floats."""

    def test_default_engine_map_returns_tuple(self):
        defaults = get_defaults()
        result = defaults["engine_map"](10000, 0.8, 90.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        torque_pct, fuel_flow_pct = result
        assert 0.0 <= torque_pct <= 1.0
        assert 0.0 <= fuel_flow_pct <= 1.0


class TestDefaultGearbox:
    """Test default_gearbox returns an int."""

    def test_default_gearbox_returns_int(self):
        defaults = get_defaults()
        result = defaults["gearbox"](10000, 200.0, 5, 0.8)
        assert isinstance(result, int)
        assert 1 <= result <= 8


class TestOutputRanges:
    """Test OUTPUT_RANGES covers all 9 non-strategy components."""

    def test_output_ranges_defined(self):
        non_strategy = [c for c in COMPONENT_FUNCTIONS if c != "strategy"]
        assert len(non_strategy) == 9
        for name in non_strategy:
            assert name in OUTPUT_RANGES, f"{name} missing from OUTPUT_RANGES"
            for key, (lo, hi) in OUTPUT_RANGES[name].items():
                assert lo < hi, f"{name}.{key} range invalid: {lo} >= {hi}"


class TestHardwareSpecs:
    """Test HARDWARE_SPECS have options."""

    def test_hardware_specs_have_options(self):
        assert "ENGINE_SPEC" in HARDWARE_SPECS
        assert "AERO_SPEC" in HARDWARE_SPECS
        assert "CHASSIS_SPEC" in HARDWARE_SPECS
        # Each category has at least one option
        for category, specs in HARDWARE_SPECS.items():
            assert len(specs) >= 1, f"{category} has no specs"
        # Aero has 3 options
        assert len(HARDWARE_SPECS["AERO_SPEC"]) == 3
        # get_hardware_spec works
        engine = get_hardware_spec("ENGINE_SPEC", "v6_1000hp")
        assert engine["max_hp"] == 1000


class TestClampOutput:
    """Test clamp_output clamps out-of-range values."""

    def test_clamp_output_works(self):
        # Below range
        result = clamp_output("gearbox", {"target_gear": -1})
        assert result["target_gear"] == 1
        # Above range
        result = clamp_output("gearbox", {"target_gear": 20})
        assert result["target_gear"] == 8
        # In range
        result = clamp_output("gearbox", {"target_gear": 5})
        assert result["target_gear"] == 5
        # Float range
        result = clamp_output("cooling", {"cooling_effort": 1.5})
        assert result["cooling_effort"] == 1.0


class TestDefaultStrategy:
    """Test default_strategy returns a dict."""

    def test_default_strategy_returns_dict(self):
        defaults = get_defaults()
        state = {"tire_wear": 0.8, "laps_left": 5, "position": 3}
        result = defaults["strategy"](state)
        assert isinstance(result, dict)
