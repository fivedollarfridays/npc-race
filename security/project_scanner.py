"""Deep import scanner for directory-based car projects.

Walks the full import graph of a car project, scanning each file for
security violations and detecting forbidden imports buried in helpers.
"""

import ast
import os

from .bot_scanner import (
    ALLOWED_IMPORTS,
    ScanResult,
    _check_calls,
    _check_dunder_attrs,
    _check_module_level_code,
    _check_semicolons,
)

__all__ = ["scan_car_project"]


def _resolve_import_to_path(
    module: str | None,
    level: int,
    current_file: str,
    project_dir: str,
) -> str | None:
    """Resolve an import statement to a file path within the project.

    Returns absolute path if the import maps to a project file, else None.
    """
    if level > 0 and module:
        base = os.path.dirname(current_file)
        for _ in range(level - 1):
            base = os.path.dirname(base)
        rel = module.replace(".", os.sep)
        candidate = os.path.join(base, rel + ".py")
        if os.path.isfile(candidate):
            return candidate
        candidate = os.path.join(base, rel, "__init__.py")
        if os.path.isfile(candidate):
            return candidate
        return None

    if level > 0 and module is None:
        return None

    if module is None:
        return None

    parts = module.split(".")
    candidate = os.path.join(project_dir, *parts) + ".py"
    if os.path.isfile(candidate):
        return candidate
    candidate = os.path.join(project_dir, *parts, "__init__.py")
    if os.path.isfile(candidate):
        return candidate
    return None


def _is_project_import(
    module: str | None, level: int, project_dir: str, current_file: str,
) -> bool:
    """Check if an import refers to a module within the project directory."""
    if level > 0:
        return True
    if module is None:
        return False
    resolved = _resolve_import_to_path(module, 0, current_file, project_dir)
    if resolved is not None:
        return True
    root = module.split(".")[0]
    if os.path.isdir(os.path.join(project_dir, root)):
        return True
    if os.path.isfile(os.path.join(project_dir, root + ".py")):
        return True
    return False


def _resolve_submodule(
    module: str | None,
    level: int,
    name: str,
    current_file: str,
    project_dir: str,
) -> str | None:
    """Resolve `from <module> import <name>` as a submodule file."""
    if level > 0 and module is None:
        base = os.path.dirname(current_file)
        candidate = os.path.join(base, name + ".py")
        if os.path.isfile(candidate):
            return candidate
        pkg = os.path.join(base, name, "__init__.py")
        if os.path.isfile(pkg):
            return pkg
        return None

    if module is None:
        return None

    if level > 0:
        base = os.path.dirname(current_file)
        for _ in range(level - 1):
            base = os.path.dirname(base)
        mod_dir = os.path.join(base, *module.split("."))
    else:
        mod_dir = os.path.join(project_dir, *module.split("."))

    candidate = os.path.join(mod_dir, name + ".py")
    if os.path.isfile(candidate):
        return candidate
    pkg = os.path.join(mod_dir, name, "__init__.py")
    if os.path.isfile(pkg):
        return pkg
    return None


def _check_imports_project(
    tree: ast.AST, filepath: str, project_dir: str,
) -> list[str]:
    """Reject imports not in ALLOWED_IMPORTS and not project-internal."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in ALLOWED_IMPORTS:
                    continue
                if _is_project_import(alias.name, 0, project_dir, filepath):
                    continue
                violations.append(
                    f"Disallowed import: '{alias.name}' "
                    f"(line {node.lineno})"
                )
        elif isinstance(node, ast.ImportFrom):
            level = node.level or 0
            if level > 0:
                continue
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            if root in ALLOWED_IMPORTS:
                continue
            if _is_project_import(node.module, 0, project_dir, filepath):
                continue
            violations.append(
                f"Module '{node.module}' not found in project "
                f"(line {node.lineno})"
            )
    return violations


def _check_file_security(
    tree: ast.AST, source: str, filepath: str, project_dir: str,
) -> list[str]:
    """Run all security checks on a parsed AST (no metadata check)."""
    violations: list[str] = []
    violations.extend(_check_imports_project(tree, filepath, project_dir))
    violations.extend(_check_calls(tree))
    violations.extend(_check_dunder_attrs(tree))
    violations.extend(_check_module_level_code(tree))
    violations.extend(_check_semicolons(tree, source))
    return violations


def _walk_imports(
    filepath: str,
    project_dir: str,
    visited: set[str],
    violations: list[str],
) -> None:
    """Recursively scan a file and follow project-internal imports."""
    real = os.path.realpath(filepath)
    if real in visited:
        return
    visited.add(real)

    rel = os.path.relpath(filepath, project_dir)

    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except OSError:
        violations.append(f"{rel}: file not found or unreadable")
        return

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        violations.append(f"{rel}: syntax error: {e}")
        return

    for v in _check_file_security(tree, source, filepath, project_dir):
        violations.append(f"{rel}: {v}")

    _follow_imports(tree, filepath, project_dir, visited, violations)


def _follow_imports(
    tree: ast.AST,
    filepath: str,
    project_dir: str,
    visited: set[str],
    violations: list[str],
) -> None:
    """Follow project-internal imports from a parsed AST."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = _resolve_import_to_path(
                    alias.name, 0, filepath, project_dir,
                )
                if target and os.path.realpath(target) not in visited:
                    _walk_imports(target, project_dir, visited, violations)
        elif isinstance(node, ast.ImportFrom):
            _follow_from_import(
                node, filepath, project_dir, visited, violations,
            )


def _follow_from_import(
    node: ast.ImportFrom,
    filepath: str,
    project_dir: str,
    visited: set[str],
    violations: list[str],
) -> None:
    """Follow a single 'from ... import ...' node."""
    mod = node.module
    level = node.level or 0

    if not _is_project_import(mod, level, project_dir, filepath):
        return

    target = _resolve_import_to_path(mod, level, filepath, project_dir)
    if target and os.path.realpath(target) not in visited:
        _walk_imports(target, project_dir, visited, violations)

    for alias in node.names:
        sub = _resolve_submodule(
            mod, level, alias.name, filepath, project_dir,
        )
        if sub and os.path.realpath(sub) not in visited:
            _walk_imports(sub, project_dir, visited, violations)


def scan_car_project(project_dir: str) -> ScanResult:
    """Scan all .py files in a car project directory, walking the import graph.

    Returns ScanResult with passed=True if clean, passed=False with violations.
    """
    violations: list[str] = []
    visited: set[str] = set()

    for dirpath, _dirs, files in os.walk(project_dir):
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(dirpath, fname)
            _walk_imports(filepath, project_dir, visited, violations)

    return ScanResult(passed=len(violations) == 0, violations=violations)
