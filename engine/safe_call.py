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


def _apply_glitch(entry, part_name, args, default_func, glitch_ctx):
    """Check for glitch after successful part call. Replace output with default if glitching."""
    if not glitch_ctx or entry["status"] not in ("ok", "clamped"):
        return entry
    ge = glitch_ctx["engine"]
    car_idx = glitch_ctx["car_idx"]
    reliability = glitch_ctx["reliability"]
    rng = glitch_ctx["rng"]
    tick = entry["tick"]
    if ge.is_glitching(part_name, car_idx):
        pass  # already active
    elif ge.should_glitch(part_name, reliability, tick, rng):
        ge.set_active_glitch(part_name, car_idx, ge.get_glitch_duration(part_name))
    else:
        return entry
    try:
        fallback = default_func(*args)
    except Exception:
        return entry
    entry["output"] = clamp_output(part_name, fallback)
    entry["status"] = "glitch"
    return entry


def _safe_call_with_timeout(part_name, func, args, default_func, tick,
                             glitch_ctx=None):
    """Call player function with 1ms timeout. Falls back to default on timeout/error."""
    if not TIMEOUT_ENABLED:
        return _safe_call_direct(part_name, func, args, default_func, tick,
                                 glitch_ctx)

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
    entry = {
        "part": part_name, "tick": tick, "output": clamped,
        "status": status, "efficiency": 1.0,  # computed later
    }
    return _apply_glitch(entry, part_name, args, default_func, glitch_ctx)


def _safe_call_direct(part_name, func, args, default_func, tick,
                       glitch_ctx=None):
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
    entry = {
        "part": part_name, "tick": tick, "output": clamped,
        "status": status, "efficiency": 1.0,
    }
    return _apply_glitch(entry, part_name, args, default_func, glitch_ctx)
