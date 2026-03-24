"""League gate validation and filtering for race cars.

Applies league detection, per-car quality validation, and filtering
before a race starts. Used by race_runner.
"""

from .league_system import (
    LEAGUE_TIERS,
    determine_league,
    generate_quality_report,
    validate_car_for_league,
)


def _detect_league(
    cars: list[dict], league: str | None,
) -> tuple[str, str]:
    """Return (effective_league, display_label) for a set of cars."""
    if league is None:
        per_car = [determine_league(c) for c in cars]
        effective = max(per_car, key=lambda t: LEAGUE_TIERS.index(t))
        return effective, f"{effective} (auto-detected)"
    return league, league


def _print_car_league_status(
    name: str, parts: list[str], qr, league: str,
) -> None:
    """Print one car's league status line."""
    n_parts = len(parts)
    if n_parts == 0:
        print(f"  {name}: 0 custom parts -> using defaults ({league} allowed)")
    else:
        part_list = ", ".join(sorted(parts))
        print(f"  {name}: {n_parts} custom parts [{part_list}]")

    # Quality details
    if qr.advisory_messages:
        for msg in qr.advisory_messages:
            print(f"    Advisory: {msg}")
    if qr.passed and not qr.blocking_violations:
        status = (
            "Advisory: clean code" if league in ("F3", "F2")
            else f"Passed {league} gate"
        )
        print(
            f"    Quality: reliability {qr.reliability_score:.2f} | "
            f"CC avg n/a | {status}"
        )


def _filter_car(car: dict, league: str | None, effective: str, verbose: bool) -> bool:
    """Validate and score a single car. Return True if it should race."""
    name = car.get("name", "Unknown")
    parts = car.get("_loaded_parts", [])
    car["league"] = effective

    if league is not None:
        vr = validate_car_for_league(car, effective)
        if not vr.passed:
            if verbose:
                print(f"  {name}: REJECTED -- {'; '.join(vr.violations)}")
            return False

    qr = generate_quality_report(car, effective)
    car["reliability_score"] = qr.reliability_score
    if verbose:
        _print_car_league_status(name, parts, qr, effective)

    if league is not None and not qr.passed:
        if verbose:
            print(f"  {name}: REJECTED -- {'; '.join(qr.blocking_violations)}")
        return False
    return True


def apply_league_gates(
    cars: list[dict], league: str | None, *, verbose: bool = False,
) -> tuple[list[dict], str]:
    """Detect/validate league, filter rejected cars.

    Returns (filtered_cars, effective_league).

    When *verbose* is False (default), only a single summary line is printed.
    When True, per-car details are shown.
    """
    effective, label = _detect_league(cars, league)

    if verbose:
        print(f"\n=== League: {label} ===")

    filtered = [c for c in cars if _filter_car(c, league, effective, verbose)]

    if not verbose:
        print(f"\n=== League: {label} -- {len(filtered)} cars validated ===")

    return filtered, effective
