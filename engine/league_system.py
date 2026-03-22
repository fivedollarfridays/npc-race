"""League system -- F3 -> F2 -> F1 -> Championship progression.

Parts are assigned to tiers based on measured sensitivity. Every part
a player unlocks produces visible results at that tier's race distance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .code_quality import compute_cyclomatic_complexity, compute_reliability_score
from .parts_api import CAR_PARTS

LEAGUE_TIERS = ["F3", "F2", "F1", "Championship"]

LEAGUE_PARTS: dict[str, list[str]] = {
    "F3": ["gearbox", "cooling", "strategy"],
    "F2": ["gearbox", "cooling", "suspension", "ers_deploy", "fuel_mix", "strategy"],
    "F1": list(CAR_PARTS),
    "Championship": list(CAR_PARTS),
}


@dataclass
class LeagueResult:
    """Outcome of validating a car against a league's part restrictions."""

    passed: bool
    league: str
    loaded_parts: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)


def determine_league(car: dict) -> str:
    """Infer league tier from loaded parts."""
    loaded = set(car.get("_loaded_parts", []))
    if not loaded:
        return "F3"

    f3_parts = set(LEAGUE_PARTS["F3"])
    f2_parts = set(LEAGUE_PARTS["F2"])

    if loaded <= f3_parts:
        return "F3"
    if loaded <= f2_parts:
        return "F2"
    # Has parts beyond F2 -- F1 or Championship
    # Championship requires multi-file project
    if car.get("_project_dir"):
        return "Championship"
    return "F1"


def validate_car_for_league(car: dict, league: str) -> LeagueResult:
    """Check if a car's parts match the league's restrictions."""
    loaded = car.get("_loaded_parts", [])
    allowed = set(LEAGUE_PARTS.get(league, CAR_PARTS))
    violations = []

    for part in loaded:
        if part not in allowed:
            violations.append(
                f"Part '{part}' is not allowed in {league} "
                f"(allowed: {', '.join(sorted(allowed))})"
            )

    return LeagueResult(
        passed=len(violations) == 0,
        league=league,
        loaded_parts=loaded,
        violations=violations,
    )


@dataclass
class QualityReport:
    """Quality gate report for a car in a given league."""

    passed: bool
    league: str
    reliability_score: float
    advisory_messages: list[str] = field(default_factory=list)
    blocking_violations: list[str] = field(default_factory=list)


def generate_quality_report(car: dict, league: str) -> QualityReport:
    """Generate quality report for a car in a given league."""
    source = car.get("_source", "")
    if not source:
        return QualityReport(passed=True, league=league, reliability_score=1.0)

    cc_per_func = compute_cyclomatic_complexity(source)
    reliability = compute_reliability_score(source)
    avg_cc = _avg_cc(cc_per_func)

    advisory = _build_advisory(cc_per_func, reliability)
    violations = _build_violations(cc_per_func, avg_cc, reliability, league)

    is_advisory = league in ("F3", "F2")
    passed = True if is_advisory else len(violations) == 0

    return QualityReport(
        passed=passed,
        league=league,
        reliability_score=reliability,
        advisory_messages=advisory,
        blocking_violations=violations,
    )


def _avg_cc(cc_per_func: dict[str, int]) -> float:
    """Average cyclomatic complexity across functions."""
    if not cc_per_func:
        return 0.0
    return sum(cc_per_func.values()) / len(cc_per_func)


def _build_advisory(cc_per_func: dict[str, int], reliability: float) -> list[str]:
    """Build informational messages about code quality."""
    messages: list[str] = []
    for func_name, cc in cc_per_func.items():
        if cc > 5:
            messages.append(
                f"Your {func_name} function has CC={cc}. "
                f"At F1 level, CC above 15 triggers glitches. "
                f"You're safe for now."
            )
    if reliability < 0.88:
        messages.append(
            f"Reliability score {reliability:.2f}. "
            f"Championship requires >= 0.88."
        )
    return messages


def _build_violations(
    cc_per_func: dict[str, int],
    avg_cc: float,
    reliability: float,
    league: str,
) -> list[str]:
    """Build blocking violations for enforced leagues (F1/Championship)."""
    if league in ("F3", "F2"):
        return []

    violations: list[str] = []

    # F1 + Championship: lint-like check (high CC functions as proxy)
    for func_name, cc in cc_per_func.items():
        if cc > 15:
            violations.append(
                f"{func_name} has cyclomatic complexity {cc} (limit 15)"
            )

    # Championship: reliability threshold
    if league == "Championship" and reliability < 0.88:
        worst = max(cc_per_func, key=cc_per_func.get) if cc_per_func else "unknown"
        worst_cc = cc_per_func.get(worst, 0)
        violations.append(
            f"Championship requires reliability >= 0.88. "
            f"Your score: {reliability:.2f}. "
            f"Reduce cyclomatic complexity in {worst} "
            f"(CC={worst_cc}, limit 15)."
        )

    return violations
