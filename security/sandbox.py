"""Runtime sandbox for car strategy() calls."""

import copy
import logging
import threading

logger = logging.getLogger(__name__)

DEFAULTS: dict = {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
VALID_TIRE_MODES: set[str] = {"conserve", "balanced", "push"}


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


def _merge_with_defaults(result: dict) -> dict:
    """Merge a partial strategy result with defaults."""
    merged = _get_defaults()
    if "throttle" in result:
        merged["throttle"] = _validate_throttle(result["throttle"])
    if "boost" in result:
        merged["boost"] = bool(result["boost"])
    if "tire_mode" in result:
        merged["tire_mode"] = _validate_tire_mode(result["tire_mode"])
    return merged


def _run_with_timeout(fn, args, timeout_sec: float):
    """Run fn(*args) in a thread with timeout. Returns (result, error)."""
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
