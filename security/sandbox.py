"""Runtime sandbox for car strategy() calls."""

import copy
import logging
import threading

logger = logging.getLogger(__name__)

DEFAULTS: dict = {
    "throttle": 1.0,
    "boost": False,
    "tire_mode": "balanced",
    "lateral_target": 0.0,
    "pit_request": False,
    "tire_compound_request": None,
    "engine_mode": "standard",
}
VALID_TIRE_MODES: set[str] = {"conserve", "balanced", "push"}
VALID_ENGINE_MODES: set[str] = {"push", "standard", "conserve"}
VALID_COMPOUNDS: set[str] = {"soft", "medium", "hard"}


def _get_defaults() -> dict:
    """Return a fresh copy of default decisions."""
    return dict(DEFAULTS)


def _validate_throttle(value: object) -> float:
    """Clamp throttle to 0.0-1.0 range."""
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULTS["throttle"]
    return max(0.0, min(1.0, f))


def _validate_tire_mode(value: object) -> str:
    """Validate tire_mode is a known string."""
    if isinstance(value, str) and value in VALID_TIRE_MODES:
        return value
    return DEFAULTS["tire_mode"]


def _validate_lateral_target(value: object) -> float:
    """Clamp lateral_target to [-1.0, 1.0]."""
    try:
        val = float(value)  # type: ignore[arg-type]
        return max(-1.0, min(1.0, val))
    except (TypeError, ValueError):
        return 0.0


def _validate_engine_mode(value: object) -> str:
    """Validate engine mode string."""
    if isinstance(value, str) and value in VALID_ENGINE_MODES:
        return value
    return "standard"


def _validate_tire_compound_request(value: object) -> str | None:
    """Validate tire compound request."""
    if value is None:
        return None
    if isinstance(value, str) and value in VALID_COMPOUNDS:
        return value
    return None


def _merge_with_defaults(result: dict) -> dict:
    """Merge a partial strategy result with defaults."""
    merged = _get_defaults()
    if "throttle" in result:
        merged["throttle"] = _validate_throttle(result["throttle"])
    if "boost" in result:
        merged["boost"] = bool(result["boost"])
    if "tire_mode" in result:
        merged["tire_mode"] = _validate_tire_mode(result["tire_mode"])
    if "lateral_target" in result:
        merged["lateral_target"] = _validate_lateral_target(result["lateral_target"])
    if "pit_request" in result:
        merged["pit_request"] = bool(result["pit_request"])
    if "tire_compound_request" in result:
        merged["tire_compound_request"] = _validate_tire_compound_request(
            result["tire_compound_request"]
        )
    if "engine_mode" in result:
        merged["engine_mode"] = _validate_engine_mode(result["engine_mode"])
    return merged


def _run_with_timeout(fn, args, timeout_sec: float):
    """Run fn(*args) in a thread with timeout. Returns (result, error).

    NOTE: Python threads cannot be forcibly killed. If a strategy enters
    an infinite loop, the daemon thread will leak and continue consuming CPU.
    This is a known limitation. For production use, consider multiprocessing.
    """
    result_holder: list = [None]
    error_holder: list[BaseException | None] = [None]

    def target():
        try:
            result_holder[0] = fn(*args)
        except BaseException as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)

    if thread.is_alive():
        return None, TimeoutError("strategy exceeded timeout")
    if error_holder[0] is not None:
        return None, error_holder[0]
    return result_holder[0], None


def safe_strategy_call(
    strategy_fn, state: dict, timeout_ms: int = 100
) -> dict:
    """Wrap a car strategy() call with safety measures.

    - Deep copies state before passing to strategy
    - Catches exceptions (returns defaults)
    - Enforces timeout (returns defaults)
    - Validates return type and values
    - Merges partial returns with defaults
    """
    frozen_state = copy.deepcopy(state)
    timeout_sec = timeout_ms / 1000.0

    raw_result, error = _run_with_timeout(strategy_fn, (frozen_state,), timeout_sec)

    if error is not None:
        if isinstance(error, TimeoutError):
            logger.warning("strategy timeout after %dms", timeout_ms)
        else:
            logger.warning("strategy exception: %s", error)
        return _get_defaults()

    if not isinstance(raw_result, dict):
        logger.warning("strategy returned non-dict: %s", type(raw_result).__name__)
        return _get_defaults()

    return _merge_with_defaults(raw_result)
