"""Tests for process-based sandbox in engine/safe_call.py."""

import time

import pytest

import engine.safe_call as sc


def _identity(x):
    """Simple function that returns its input."""
    return x


def _default(x):
    """Default fallback function."""
    return 0.5


# --- Cycle 1: Normal call works through process path ---

def test_process_normal_call_works():
    """A normal function returns correct output via process-based sandbox."""
    original = sc.PROCESS_TIMEOUT_S
    sc.PROCESS_TIMEOUT_S = 0.5  # 500ms — generous for process startup
    try:
        result = sc._safe_call_with_process(
            part_name="throttle",
            func=_identity,
            args=(0.8,),
            default_func=_default,
            tick=1,
        )
    finally:
        sc.PROCESS_TIMEOUT_S = original
    assert result["status"] == "ok"
    assert result["output"] == 0.8
    assert result["part"] == "throttle"
    assert result["tick"] == 1


# --- Cycle 2: Infinite loop killed ---

def _infinite_loop(x):
    """Function that never returns."""
    while True:
        pass


def test_process_kills_infinite_loop():
    """An infinite loop in player code is killed and returns timeout."""
    # Use a generous process timeout for this test
    original = sc.PROCESS_TIMEOUT_S
    sc.PROCESS_TIMEOUT_S = 0.05  # 50ms
    try:
        start = time.monotonic()
        result = sc._safe_call_with_process(
            part_name="throttle",
            func=_infinite_loop,
            args=(0.8,),
            default_func=_default,
            tick=1,
        )
        elapsed = time.monotonic() - start
    finally:
        sc.PROCESS_TIMEOUT_S = original

    assert result["status"] == "timeout"
    assert result["output"] == 0.5  # default_func returns 0.5
    assert elapsed < 1.0, f"Should finish quickly, took {elapsed:.2f}s"


# --- Cycle 3: Exception handled ---

def _raise_error(x):
    """Function that always raises."""
    raise ValueError("bad input")


def test_process_exception_handled():
    """An exception in the child process returns error status with default output."""
    original = sc.PROCESS_TIMEOUT_S
    sc.PROCESS_TIMEOUT_S = 0.5  # 500ms — generous for process startup
    try:
        result = sc._safe_call_with_process(
            part_name="throttle",
            func=_raise_error,
            args=(0.8,),
            default_func=_default,
            tick=1,
        )
    finally:
        sc.PROCESS_TIMEOUT_S = original
    assert result["status"] == "error"
    assert result["output"] == 0.5  # default_func returns 0.5
    assert "bad input" in result["error"]


# --- Cycle 4: USE_PROCESS flag routing ---

@pytest.mark.smoke
def test_use_process_flag_routes_to_process(monkeypatch):
    """When USE_PROCESS=True, _safe_call_with_timeout dispatches to process path."""
    calls = []

    def mock_process_call(*args, **kwargs):
        calls.append("process")
        return {"part": "throttle", "tick": 1, "output": 0.8,
                "status": "ok", "efficiency": 1.0}

    monkeypatch.setattr(sc, "USE_PROCESS", True)
    monkeypatch.setattr(sc, "_safe_call_with_process", mock_process_call)

    result = sc._safe_call_with_timeout(
        part_name="throttle",
        func=_identity,
        args=(0.8,),
        default_func=_default,
        tick=1,
    )
    assert calls == ["process"]
    assert result["status"] == "ok"


def test_use_process_false_uses_threads(monkeypatch):
    """When USE_PROCESS=False and TIMEOUT_ENABLED=True, uses thread path (default)."""
    monkeypatch.setattr(sc, "USE_PROCESS", False)
    monkeypatch.setattr(sc, "TIMEOUT_ENABLED", True)

    result = sc._safe_call_with_timeout(
        part_name="throttle",
        func=_identity,
        args=(0.8,),
        default_func=_default,
        tick=1,
    )
    # Thread path works correctly for normal functions
    assert result["status"] == "ok"
    assert result["output"] == 0.8
