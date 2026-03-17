"""Tests for security/sandbox.py — safe_strategy_call wrapper."""

import time

from security.sandbox import safe_strategy_call

DEFAULTS = {
    "throttle": 1.0,
    "boost": False,
    "tire_mode": "balanced",
    "lateral_target": 0.0,
    "pit_request": False,
    "tire_compound_request": None,
    "engine_mode": "standard",
}


class TestSafeStrategyCallBasic:
    """Cycle 1: basic happy-path returns."""

    def test_returns_dict(self):
        def good_strategy(state):
            return {"throttle": 0.8, "boost": True, "tire_mode": "push"}

        result = safe_strategy_call(good_strategy, {})
        assert isinstance(result, dict)

    def test_returns_strategy_values(self):
        def good_strategy(state):
            return {"throttle": 0.5, "boost": True, "tire_mode": "conserve"}

        result = safe_strategy_call(good_strategy, {})
        assert result["throttle"] == 0.5
        assert result["boost"] is True
        assert result["tire_mode"] == "conserve"

    def test_state_passed_to_strategy(self):
        def check_state(state):
            assert state["lap"] == 2
            return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}

        result = safe_strategy_call(check_state, {"lap": 2})
        assert result["throttle"] == 1.0


class TestSafeStrategyCallDefaults:
    """Cycle 2: returns defaults on exception."""

    def test_exception_returns_defaults(self):
        def bad_strategy(state):
            raise ValueError("oops")

        result = safe_strategy_call(bad_strategy, {})
        assert result == DEFAULTS

    def test_runtime_error_returns_defaults(self):
        def exploding(state):
            raise RuntimeError("boom")

        result = safe_strategy_call(exploding, {})
        assert result == DEFAULTS

    def test_state_not_mutated(self):
        """Deep copy protects caller's state."""
        def mutator(state):
            state["lap"] = 999
            state["me"] = "evil"
            return {"throttle": 0.5, "boost": False, "tire_mode": "balanced"}

        original = {"lap": 1, "speed": 100.0}
        safe_strategy_call(mutator, original)
        assert original["lap"] == 1
        assert "me" not in original

    def test_nested_state_not_mutated(self):
        def nested_mutator(state):
            state["nearby_cars"][0]["speed"] = 0
            return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}

        original = {"nearby_cars": [{"speed": 50.0, "name": "rival"}]}
        safe_strategy_call(nested_mutator, original)
        assert original["nearby_cars"][0]["speed"] == 50.0


class TestSafeStrategyCallTimeout:
    """Cycle 3: returns defaults on timeout."""

    def test_timeout_returns_defaults(self):
        def slow_strategy(state):
            time.sleep(3)
            return {"throttle": 0.5, "boost": True, "tire_mode": "push"}

        result = safe_strategy_call(slow_strategy, {}, timeout_ms=50)
        assert result == DEFAULTS

    def test_fast_strategy_within_timeout(self):
        def fast_strategy(state):
            time.sleep(0.01)
            return {"throttle": 0.7, "boost": False, "tire_mode": "conserve"}

        result = safe_strategy_call(fast_strategy, {}, timeout_ms=500)
        assert result["throttle"] == 0.7
        assert result["tire_mode"] == "conserve"


class TestSafeStrategyCallBadReturnType:
    """Cycle 4: returns defaults on non-dict return."""

    def test_none_returns_defaults(self):
        result = safe_strategy_call(lambda s: None, {})
        assert result == DEFAULTS

    def test_string_returns_defaults(self):
        result = safe_strategy_call(lambda s: "bad", {})
        assert result == DEFAULTS

    def test_list_returns_defaults(self):
        result = safe_strategy_call(lambda s: [1, 2, 3], {})
        assert result == DEFAULTS

    def test_int_returns_defaults(self):
        result = safe_strategy_call(lambda s: 42, {})
        assert result == DEFAULTS


class TestSafeStrategyCallPartialMerge:
    """Cycle 5: merges partial returns with defaults."""

    def test_missing_throttle_filled(self):
        result = safe_strategy_call(
            lambda s: {"boost": True, "tire_mode": "push"}, {}
        )
        assert result["throttle"] == 1.0  # default
        assert result["boost"] is True
        assert result["tire_mode"] == "push"

    def test_missing_boost_filled(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 0.5, "tire_mode": "conserve"}, {}
        )
        assert result["boost"] is False  # default

    def test_missing_tire_mode_filled(self):
        result = safe_strategy_call(lambda s: {"throttle": 0.3}, {})
        assert result["tire_mode"] == "balanced"  # default

    def test_empty_dict_returns_all_defaults(self):
        result = safe_strategy_call(lambda s: {}, {})
        assert result == DEFAULTS


class TestSafeStrategyCallValidation:
    """Cycle 6: validates throttle range and tire_mode enum."""

    def test_throttle_clamped_above_one(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 5.0, "boost": False, "tire_mode": "balanced"}, {}
        )
        assert result["throttle"] == 1.0

    def test_throttle_clamped_below_zero(self):
        result = safe_strategy_call(
            lambda s: {"throttle": -2.0, "boost": False, "tire_mode": "balanced"}, {}
        )
        assert result["throttle"] == 0.0

    def test_throttle_non_numeric_uses_default(self):
        result = safe_strategy_call(
            lambda s: {"throttle": "fast", "boost": False, "tire_mode": "balanced"}, {}
        )
        assert result["throttle"] == 1.0

    def test_invalid_tire_mode_uses_default(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "turbo"}, {}
        )
        assert result["tire_mode"] == "balanced"

    def test_tire_mode_non_string_uses_default(self):
        result = safe_strategy_call(
            lambda s: {"throttle": 1.0, "boost": False, "tire_mode": 42}, {}
        )
        assert result["tire_mode"] == "balanced"

    def test_valid_tire_modes_accepted(self):
        for mode in ("conserve", "balanced", "push"):
            result = safe_strategy_call(
                lambda s, m=mode: {"throttle": 1.0, "boost": False, "tire_mode": m},
                {},
            )
            assert result["tire_mode"] == mode
