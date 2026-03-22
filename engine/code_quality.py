"""Code quality analysis -- AST-based metrics for car reliability scoring.

Better code -> higher reliability -> fewer glitches -> faster car.
"""

import ast


def compute_cyclomatic_complexity(source: str) -> dict[str, int]:
    """Compute cyclomatic complexity per function. CC = 1 + decision points."""
    tree = ast.parse(source)
    result: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            cc = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    cc += 1
                elif isinstance(child, ast.BoolOp):
                    cc += len(child.values) - 1
            result[node.name] = cc
    return result


def compute_cognitive_complexity(source: str) -> dict[str, int]:
    """Compute cognitive complexity per function (nesting-aware)."""
    tree = ast.parse(source)
    result: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            result[node.name] = _cognitive_walk(node, 0)
    return result


def _cognitive_walk(node: ast.AST, nesting: int) -> int:
    """Walk AST counting cognitive complexity with nesting penalty."""
    total = 0
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While)):
            total += 1 + nesting  # base + nesting penalty
            total += _cognitive_walk(child, nesting + 1)
        elif isinstance(child, ast.ExceptHandler):
            total += 1 + nesting
            total += _cognitive_walk(child, nesting + 1)
        elif isinstance(child, ast.BoolOp):
            total += len(child.values) - 1
        else:
            total += _cognitive_walk(child, nesting)
    return total


def get_function_lengths(source: str) -> dict[str, int]:
    """Map function names to line counts."""
    tree = ast.parse(source)
    result: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            end = node.end_lineno or node.lineno
            result[node.name] = end - node.lineno + 1
    return result


def check_type_hints(source: str) -> float:
    """Fraction of functions with type annotations (0.0-1.0)."""
    tree = ast.parse(source)
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not functions:
        return 1.0
    hinted = sum(
        1 for f in functions
        if f.returns is not None or any(a.annotation for a in f.args.args)
    )
    return hinted / len(functions)


def compute_reliability_score(source: str) -> float:
    """Aggregate reliability score from code quality metrics. Returns 0.50-1.00."""
    cc = compute_cyclomatic_complexity(source)
    cog = compute_cognitive_complexity(source)
    lengths = get_function_lengths(source)
    hints = check_type_hints(source)

    reliability = 1.0

    # CC penalty (avg across functions)
    if cc:
        avg_cc = sum(cc.values()) / len(cc)
        if avg_cc > 15:
            reliability -= 0.15
        elif avg_cc > 10:
            reliability -= 0.10
        elif avg_cc > 5:
            reliability -= 0.05

    # Cognitive complexity penalty (max function)
    if cog:
        max_cog = max(cog.values())
        if max_cog > 25:
            reliability -= 0.12
        elif max_cog > 10:
            reliability -= 0.08
        elif max_cog > 5:
            reliability -= 0.04

    # Function length penalty (max)
    if lengths:
        max_len = max(lengths.values())
        if max_len > 50:
            reliability -= 0.05
        elif max_len < 30:
            reliability += 0.01  # compact bonus

    # Type hint bonus/penalty
    if hints >= 0.8:
        reliability += 0.02
    elif hints < 0.2:
        reliability -= 0.05

    return max(0.50, min(1.00, reliability))
