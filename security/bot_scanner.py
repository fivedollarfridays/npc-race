"""AST pre-scan for car .py files — ALLOWLIST model.

Scans car source files using ast.parse() + ast.walk() to detect:
- Any import not in ALLOWED_IMPORTS (allowlist, not blocklist)
- Dangerous built-in calls (eval, exec, compile, etc.)
- Blocked dunder attribute access
- Non-declarative module-level code
- Semicolons in strategy() body
- Car metadata validation (name, color, stats, budget)
"""

import ast
import re
from dataclasses import dataclass, field

__all__ = [
    "ALLOWED_IMPORTS",
    "BLOCKED_CALLS",
    "BLOCKED_DUNDER_ATTRS",
    "ScanResult",
    "scan_car_source",
    "scan_car_file",
    "scan_car_project",
]

ALLOWED_IMPORTS: frozenset[str] = frozenset({
    "math", "random", "collections", "itertools", "functools", "json",
})

BLOCKED_CALLS: frozenset[str] = frozenset({
    "eval", "exec", "compile", "__import__",
    "getattr", "setattr", "delattr",
    "globals", "locals", "vars",
    "type", "dir",
})

BLOCKED_DUNDER_ATTRS: frozenset[str] = frozenset({
    "__globals__", "__builtins__", "__subclasses__", "__mro__",
    "__bases__", "__class__", "__code__", "__closure__",
})

STAT_FIELDS = ("POWER", "GRIP", "WEIGHT", "AERO", "BRAKES")
STAT_BUDGET = 100

_STRING_RE = re.compile(r'''("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')''')


@dataclass
class ScanResult:
    """Result of scanning a car file."""

    passed: bool
    violations: list[str] = field(default_factory=list)


# --- AST checks ---


def _check_imports(tree: ast.AST) -> list[str]:
    """Reject any import not in ALLOWED_IMPORTS."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    violations.append(
                        f"Disallowed import: '{alias.name}' (line {node.lineno})"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                root = node.module.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    violations.append(
                        f"Disallowed import: 'from {node.module} import ...' "
                        f"(line {node.lineno})"
                    )
    return violations


def _is_safe_data_path(path: str) -> bool:
    """Check if a file path is safe for car data access."""
    if ".." in path:
        return False
    if not path.startswith("cars/data/"):
        return False
    if not path.endswith(".json"):
        return False
    parts = path.split("/")
    if len(parts) != 3:  # cars/data/filename.json
        return False
    # Reject empty filenames, null bytes, or non-alphanumeric characters
    filename = parts[2]
    if not re.match(r"^[a-zA-Z0-9_-]+\.json$", filename):
        return False
    return True


def _check_calls(tree: ast.AST) -> list[str]:
    """Find dangerous function/method calls."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr

        if name is None:
            continue

        # Path-gated open() — only string literals matching cars/data/*.json
        if name == "open":
            if (node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                    and _is_safe_data_path(node.args[0].value)):
                continue
            violations.append(
                f"Line {node.lineno}: open() only allowed for "
                f"cars/data/*.json paths"
            )
            continue

        if name in BLOCKED_CALLS:
            violations.append(
                f"Blocked call: '{name}()' (line {node.lineno})"
            )
    return violations


def _check_dunder_attrs(tree: ast.AST) -> list[str]:
    """Find blocked dunder attribute access."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_DUNDER_ATTRS:
            violations.append(
                f"Blocked dunder attr: '{node.attr}' (line {node.lineno})"
            )
    return violations


def _check_module_level_code(tree: ast.Module) -> list[str]:
    """Flag non-declarative module-level statements."""
    violations: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        if isinstance(node, ast.Pass):
            continue
        # Docstrings
        if (isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue
        # if __name__ == "__main__":
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "__name__"
                    and len(test.ops) == 1
                    and isinstance(test.ops[0], ast.Eq)
                    and len(test.comparators) == 1
                    and isinstance(test.comparators[0], ast.Constant)
                    and test.comparators[0].value == "__main__"):
                continue
        violations.append(
            f"Blocked top-level statement (line {node.lineno}): "
            f"only imports, assignments, and definitions allowed"
        )
    return violations


def _check_semicolons(tree: ast.AST, source: str) -> list[str]:
    """Flag semicolon statement chaining in strategy() body."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "strategy":
            lines = source.splitlines()
            start = node.body[0].lineno if node.body else node.lineno
            end = node.end_lineno or start
            for lineno in range(start, end + 1):
                line = lines[lineno - 1].strip()
                if line.startswith("#"):
                    continue
                cleaned = _STRING_RE.sub("", line)
                if ";" in cleaned:
                    violations.append(
                        f"Semicolon chaining detected (line {lineno})"
                    )
    return violations


# --- Car metadata validation ---


def _parse_top_level_assignments(tree: ast.Module) -> dict[str, object]:
    """Extract name→value from top-level constant assignments (including negatives)."""
    assignments: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if isinstance(node.value, ast.Constant):
                assignments[target.id] = node.value.value
            elif (isinstance(node.value, ast.UnaryOp)
                  and isinstance(node.value.op, ast.USub)
                  and isinstance(node.value.operand, ast.Constant)):
                assignments[target.id] = -node.value.operand.value
    return assignments


def _check_car_metadata(tree: ast.Module) -> list[str]:
    """Validate CAR_NAME, CAR_COLOR, stats, and budget from AST constants."""
    violations: list[str] = []
    assignments = _parse_top_level_assignments(tree)

    if "CAR_NAME" not in assignments:
        violations.append("Missing CAR_NAME assignment")
    elif not isinstance(assignments["CAR_NAME"], str) or not assignments["CAR_NAME"]:
        violations.append("CAR_NAME must be a non-empty string")

    if "CAR_COLOR" not in assignments:
        violations.append("Missing CAR_COLOR assignment")
    else:
        color = assignments["CAR_COLOR"]
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            violations.append(
                f"CAR_COLOR must be valid hex (#RRGGBB), got '{color}'"
            )

    stat_total = 0
    for stat in STAT_FIELDS:
        if stat not in assignments:
            violations.append(f"Missing stat: {stat}")
            continue
        val = assignments[stat]
        if not isinstance(val, (int, float)):
            violations.append(f"{stat} must be numeric, got {type(val).__name__}")
            continue
        if val < 0:
            violations.append(f"{stat} must not be negative, got {val}")
        stat_total += val

    all_stats_ok = all(
        stat in assignments and isinstance(assignments[stat], (int, float))
        for stat in STAT_FIELDS
    )
    if all_stats_ok and stat_total > STAT_BUDGET:
        violations.append(
            f"Stat budget {stat_total} exceeds {STAT_BUDGET} "
            f"(over by {stat_total - STAT_BUDGET})"
        )

    return violations


# --- Public API ---


def scan_car_source(source: str) -> ScanResult:
    """Scan car source code for security violations and metadata issues.

    Returns ScanResult with passed=True if clean, passed=False with reasons.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return ScanResult(passed=False, violations=[f"Syntax error: {e}"])

    violations: list[str] = []
    violations.extend(_check_imports(tree))
    violations.extend(_check_calls(tree))
    violations.extend(_check_dunder_attrs(tree))
    violations.extend(_check_module_level_code(tree))
    violations.extend(_check_semicolons(tree, source))
    violations.extend(_check_car_metadata(tree))

    return ScanResult(passed=len(violations) == 0, violations=violations)


def scan_car_file(path: str) -> ScanResult:
    """Scan a car file on disk for security violations.

    Returns ScanResult with passed/failed + reasons.
    """
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        return ScanResult(passed=False, violations=[f"Failed to read file: {e}"])

    return scan_car_source(source)


# Re-export from project_scanner (import at bottom to avoid circular import)
from security.project_scanner import scan_car_project  # noqa: E402, F811
