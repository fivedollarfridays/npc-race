"""Safe-call wrappers for player function invocation.

Provides timeout-guarded and direct call modes so that player code
cannot hang the engine or crash it with unhandled exceptions.
"""

import threading
from .parts_api import clamp_output

# Timeout for player function calls (seconds)
CALL_TIMEOUT_S = 0.001  # 1ms

# Set False to skip thread overhead (for batch testing / calibration)
TIMEOUT_ENABLED = True


def _safe_call_with_timeout(part_name, func, args, default_func, tick):
    """Call player function with 1ms timeout. Falls back to default on timeout/error."""
    if not TIMEOUT_ENABLED:
        return _safe_call_direct(part_name, func, args, default_func, tick)

    result_box = [None]
    error_box = [None]

    def _run():
        try:
            result_box[0] = func(*args)
        except Exception as exc:
            error_box[0] = str(exc)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=CALL_TIMEOUT_S)

    if thread.is_alive():
        # Timeout — use default
        try:
            fallback = default_func(*args)
        except Exception:
            fallback = None
        clamped = clamp_output(part_name, fallback) if fallback is not None else None
        return {
            "part": part_name, "tick": tick, "output": clamped,
            "status": "timeout", "efficiency": 0.85,
        }

    if error_box[0] is not None:
        try:
            fallback = default_func(*args)
        except Exception:
            fallback = None
        clamped = clamp_output(part_name, fallback) if fallback is not None else None
        return {
            "part": part_name, "tick": tick, "output": clamped,
            "status": "error", "efficiency": 0.85, "error": error_box[0],
        }

    raw = result_box[0]
    clamped = clamp_output(part_name, raw)
    status = "clamped" if clamped != raw else "ok"
    return {
        "part": part_name, "tick": tick, "output": clamped,
        "status": status, "efficiency": 1.0,  # computed later
    }


def _safe_call_direct(part_name, func, args, default_func, tick):
    """Direct call without thread — for trusted code / batch testing."""
    try:
        raw = func(*args)
    except Exception as exc:
        try:
            fallback = default_func(*args)
        except Exception:
            fallback = None
        clamped = clamp_output(part_name, fallback) if fallback is not None else None
        return {
            "part": part_name, "tick": tick, "output": clamped,
            "status": "error", "efficiency": 0.85, "error": str(exc),
        }
    clamped = clamp_output(part_name, raw)
    status = "clamped" if clamped != raw else "ok"
    return {
        "part": part_name, "tick": tick, "output": clamped,
        "status": status, "efficiency": 1.0,
    }
