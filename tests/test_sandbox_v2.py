"""Tests for sandbox.py v2 -- new strategy return fields."""

from security.sandbox import safe_strategy_call


class TestNewFieldDefaults:
    """Old strategies returning only throttle/boost/tire_mode get correct defaults."""

    def test_old_strategy_gets_lateral_target_default(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 0.8, "boost": False, "tire_mode": "push"}, {}
        )
        assert result["lateral_target"] == 0.0

    def test_old_strategy_gets_pit_request_default(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}, {}
        )
        assert result["pit_request"] is False

    def test_old_strategy_gets_tire_compound_request_default(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}, {}
        )
        assert result["tire_compound_request"] is None

    def test_old_strategy_gets_engine_mode_default(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}, {}
        )
        assert result["engine_mode"] == "standard"

    def test_empty_dict_has_all_new_defaults(self):
        result = safe_strategy_call(lambda s: {}, {})
        assert result["lateral_target"] == 0.0
        assert result["pit_request"] is False
        assert result["tire_compound_request"] is None
        assert result["engine_mode"] == "standard"


class TestLateralTargetValidation:
    """lateral_target clamped to [-1.0, 1.0], invalid defaults to 0.0."""

    def test_lateral_target_positive_clamped(self):
        result = safe_strategy_call(
            lambda s: {"lateral_target": 2.0}, {}
        )
        assert result["lateral_target"] == 1.0

    def test_lateral_target_negative_clamped(self):
        result = safe_strategy_call(
            lambda s: {"lateral_target": -3.0}, {}
        )
        assert result["lateral_target"] == -1.0

    def test_lateral_target_invalid_string_defaults(self):
        result = safe_strategy_call(
            lambda s: {"lateral_target": "invalid"}, {}
        )
        assert result["lateral_target"] == 0.0

    def test_lateral_target_valid_value_accepted(self):
        result = safe_strategy_call(
            lambda s: {"lateral_target": 0.5}, {}
        )
        assert result["lateral_target"] == 0.5

    def test_lateral_target_none_defaults(self):
        result = safe_strategy_call(
            lambda s: {"lateral_target": None}, {}
        )
        assert result["lateral_target"] == 0.0


class TestEngineModeValidation:
    """engine_mode must be push/standard/conserve, invalid defaults to standard."""

    def test_engine_mode_invalid_defaults(self):
        result = safe_strategy_call(
            lambda s: {"engine_mode": "invalid"}, {}
        )
        assert result["engine_mode"] == "standard"

    def test_engine_mode_push_accepted(self):
        result = safe_strategy_call(
            lambda s: {"engine_mode": "push"}, {}
        )
        assert result["engine_mode"] == "push"

    def test_engine_mode_conserve_accepted(self):
        result = safe_strategy_call(
            lambda s: {"engine_mode": "conserve"}, {}
        )
        assert result["engine_mode"] == "conserve"

    def test_engine_mode_non_string_defaults(self):
        result = safe_strategy_call(
            lambda s: {"engine_mode": 42}, {}
        )
        assert result["engine_mode"] == "standard"


class TestTireCompoundRequestValidation:
    """tire_compound_request must be soft/medium/hard or None."""

    def test_tire_compound_request_soft_accepted(self):
        result = safe_strategy_call(
            lambda s: {"tire_compound_request": "soft"}, {}
        )
        assert result["tire_compound_request"] == "soft"

    def test_tire_compound_request_medium_accepted(self):
        result = safe_strategy_call(
            lambda s: {"tire_compound_request": "medium"}, {}
        )
        assert result["tire_compound_request"] == "medium"

    def test_tire_compound_request_hard_accepted(self):
        result = safe_strategy_call(
            lambda s: {"tire_compound_request": "hard"}, {}
        )
        assert result["tire_compound_request"] == "hard"

    def test_tire_compound_request_invalid_defaults_none(self):
        result = safe_strategy_call(
            lambda s: {"tire_compound_request": "invalid"}, {}
        )
        assert result["tire_compound_request"] is None

    def test_tire_compound_request_non_string_defaults_none(self):
        result = safe_strategy_call(
            lambda s: {"tire_compound_request": 42}, {}
        )
        assert result["tire_compound_request"] is None

    def test_tire_compound_request_none_accepted(self):
        result = safe_strategy_call(
            lambda s: {"tire_compound_request": None}, {}
        )
        assert result["tire_compound_request"] is None


class TestPitRequestValidation:
    """pit_request is coerced to bool, defaults to False."""

    def test_pit_request_true_works(self):
        result = safe_strategy_call(
            lambda s: {"pit_request": True}, {}
        )
        assert result["pit_request"] is True

    def test_pit_request_defaults_false(self):
        result = safe_strategy_call(lambda s: {}, {})
        assert result["pit_request"] is False

    def test_pit_request_truthy_coerced(self):
        result = safe_strategy_call(
            lambda s: {"pit_request": 1}, {}
        )
        assert result["pit_request"] is True

    def test_pit_request_falsy_coerced(self):
        result = safe_strategy_call(
            lambda s: {"pit_request": 0}, {}
        )
        assert result["pit_request"] is False
