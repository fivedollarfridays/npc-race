"""Unit tests for engine/safe_call.py — timeout and direct call wrappers.

Process-based sandbox is tested separately in test_process_sandbox.py.
These tests cover the thread-based timeout and direct call paths.
"""

import time
from unittest.mock import patch

import engine.safe_call as sc
from engine.safe_call import _safe_call_direct, _safe_call_with_timeout


def _identity(*args):
    return args[0] if len(args) == 1 else args


def _default_gearbox(*args):
    return 4


class TestSafeCallDirect:
    """Tests for _safe_call_direct — no timeout, trusted code path."""

    def test_normal_function_returns_ok(self):
        result = _safe_call_direct("gearbox", lambda *a: 5, (0, 0, 3, 1.0),
                                   _default_gearbox, tick=10)
        assert result["status"] == "ok"
        assert result["output"] == 5
        assert result["tick"] == 10

    def test_exception_returns_error_with_fallback(self):
        def _explode(*a):
            raise ValueError("boom")

        result = _safe_call_direct("gearbox", _explode, (0, 0, 3, 1.0),
                                   _default_gearbox, tick=5)
        assert result["status"] == "error"
        assert "boom" in result["error"]
        # Fallback to default
        assert result["output"] == 4

    def test_clamped_status_when_output_out_of_range(self):
        # Gearbox valid range is 1-8; returning 99 should be clamped
        result = _safe_call_direct("gearbox", lambda *a: 99, (0, 0, 3, 1.0),
                                   _default_gearbox, tick=1)
        assert result["status"] == "clamped"
        assert result["output"] != 99


class TestSafeCallWithTimeout:
    """Tests for _safe_call_with_timeout — thread-based timeout path."""

    def test_normal_function_succeeds(self):
        with patch.object(sc, "TIMEOUT_ENABLED", True), \
             patch.object(sc, "USE_PROCESS", False):
            result = _safe_call_with_timeout(
                "gearbox", lambda *a: 5, (0, 0, 3, 1.0),
                _default_gearbox, tick=10)
        assert result["status"] == "ok"
        assert result["output"] == 5

    def test_timeout_returns_fallback(self):
        def _slow(*a):
            time.sleep(5)
            return 5

        with patch.object(sc, "TIMEOUT_ENABLED", True), \
             patch.object(sc, "USE_PROCESS", False), \
             patch.object(sc, "CALL_TIMEOUT_S", 0.001):
            result = _safe_call_with_timeout(
                "gearbox", _slow, (0, 0, 3, 1.0),
                _default_gearbox, tick=7)
        assert result["status"] == "timeout"
        assert result["efficiency"] == 0.85
        # Fallback output from default_gearbox
        assert result["output"] == 4

    def test_timeout_disabled_routes_to_direct(self):
        """When TIMEOUT_ENABLED=False, should use direct call path."""
        with patch.object(sc, "TIMEOUT_ENABLED", False):
            result = _safe_call_with_timeout(
                "gearbox", lambda *a: 6, (0, 0, 3, 1.0),
                _default_gearbox, tick=3)
        assert result["status"] == "ok"
        assert result["output"] == 6

    def test_error_in_function_returns_error_status(self):
        def _explode(*a):
            raise RuntimeError("kaboom")

        with patch.object(sc, "TIMEOUT_ENABLED", True), \
             patch.object(sc, "USE_PROCESS", False):
            result = _safe_call_with_timeout(
                "gearbox", _explode, (0, 0, 3, 1.0),
                _default_gearbox, tick=2)
        assert result["status"] == "error"
        assert "kaboom" in result["error"]
