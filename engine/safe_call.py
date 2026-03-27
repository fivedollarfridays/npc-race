"""Safe-call wrappers for player function invocation.

Provides timeout-guarded and direct call modes so that player code
cannot hang the engine or crash it with unhandled exceptions.
"""

import multiprocessing
import threading
from .parts_api import clamp_output

# Timeout for player function calls (seconds)
CALL_TIMEOUT_S = 0.001  # 1ms

# Set False to skip thread overhead (for batch testing / calibration)
TIMEOUT_ENABLED = True

# Set True for server-side execution (can kill runaway processes)
USE_PROCESS = False

# Longer timeout for process path (accounts for process creation overhead)
PROCESS_TIMEOUT_S = CALL_TIMEOUT_S * 10  # 10ms


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
    if USE_PROCESS:
        return _safe_call_with_process(part_name, func, args, default_func,
                                       tick, glitch_ctx)

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
        return _make_timeout_result(part_name, default_func, args, tick)

    if error_box[0] is not None:
        return _make_error_result(part_name, default_func, args, tick,
                                  error_box[0])

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


def _process_worker(queue, fn, call_args):
    """Worker target for process-based sandbox."""
    try:
        output = fn(*call_args)
        queue.put(("ok", output))
    except Exception as e:
        queue.put(("error", str(e)))


def _safe_call_with_process(part_name, func, args, default_func, tick,
                             glitch_ctx=None):
    """Process-based timeout that can kill runaway code via Process.kill()."""
    result_queue = multiprocessing.Queue()
    proc = multiprocessing.Process(
        target=_process_worker, args=(result_queue, func, args),
    )
    proc.start()
    proc.join(timeout=PROCESS_TIMEOUT_S)

    if proc.is_alive():
        proc.kill()
        proc.join()
        return _make_timeout_result(part_name, default_func, args, tick)

    try:
        status, output = result_queue.get_nowait()
    except Exception:
        return _make_timeout_result(part_name, default_func, args, tick)

    if status == "error":
        return _make_error_result(part_name, default_func, args, tick, output)

    clamped = clamp_output(part_name, output)
    result_status = "clamped" if clamped != output else "ok"
    entry = {
        "part": part_name, "tick": tick, "output": clamped,
        "status": result_status, "efficiency": 1.0,
    }
    return _apply_glitch(entry, part_name, args, default_func, glitch_ctx)


def _make_timeout_result(part_name, default_func, args, tick):
    """Build a timeout result entry using the default function."""
    try:
        fallback = default_func(*args)
    except Exception:
        fallback = None
    clamped = clamp_output(part_name, fallback) if fallback is not None else None
    return {
        "part": part_name, "tick": tick, "output": clamped,
        "status": "timeout", "efficiency": 0.85,
    }


def _make_error_result(part_name, default_func, args, tick, error_msg):
    """Build an error result entry using the default function."""
    try:
        fallback = default_func(*args)
    except Exception:
        fallback = None
    clamped = clamp_output(part_name, fallback) if fallback is not None else None
    return {
        "part": part_name, "tick": tick, "output": clamped,
        "status": "error", "efficiency": 0.85, "error": error_msg,
    }
