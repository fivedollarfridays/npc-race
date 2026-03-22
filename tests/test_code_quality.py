"""Tests for engine.code_quality -- AST-based code quality metrics."""

import textwrap
from engine.code_quality import (
    compute_cyclomatic_complexity,
    compute_cognitive_complexity,
    get_function_lengths,
    check_type_hints,
    compute_reliability_score,
)


class TestCyclomaticComplexity:
    def test_simple_function(self):
        source = "def foo(x):\n    return x + 1\n"
        assert compute_cyclomatic_complexity(source) == {"foo": 1}

    def test_branches(self):
        source = textwrap.dedent("""
            def bar(x):
                if x > 0:
                    return x
                elif x < 0:
                    return -x
                else:
                    return 0
        """)
        result = compute_cyclomatic_complexity(source)
        assert result["bar"] == 3  # 1 base + if + elif

    def test_loops_and_logic(self):
        source = textwrap.dedent("""
            def baz(items):
                total = 0
                for item in items:
                    if item > 0 and item < 100:
                        total += item
                return total
        """)
        result = compute_cyclomatic_complexity(source)
        assert result["baz"] == 4  # 1 + for + if + and


class TestCognitiveComplexity:
    def test_flat_function(self):
        source = "def foo(x):\n    return x + 1\n"
        assert compute_cognitive_complexity(source) == {"foo": 0}

    def test_nested_branches(self):
        source = textwrap.dedent("""
            def nested(x, y):
                if x > 0:
                    if y > 0:
                        return x + y
                return 0
        """)
        result = compute_cognitive_complexity(source)
        # if: +1, nested if: +2 (1 + 1 nesting)
        assert result["nested"] >= 3


class TestFunctionLengths:
    def test_single_function(self):
        source = "def foo(x):\n    return x\n"
        result = get_function_lengths(source)
        assert result["foo"] == 2

    def test_multiple_functions(self):
        source = "def a():\n    pass\n\ndef b():\n    x = 1\n    y = 2\n    return x + y\n"
        result = get_function_lengths(source)
        assert result["a"] == 2
        assert result["b"] == 4


class TestTypeHints:
    def test_no_hints(self):
        source = "def foo(x):\n    return x\n"
        assert check_type_hints(source) == 0.0

    def test_full_hints(self):
        source = "def foo(x: int) -> int:\n    return x\n"
        assert check_type_hints(source) == 1.0

    def test_partial_hints(self):
        source = "def a(x: int) -> int:\n    pass\n\ndef b(x):\n    pass\n"
        assert check_type_hints(source) == 0.5


class TestReliabilityScore:
    def test_clean_code_high_reliability(self):
        source = textwrap.dedent("""
            def engine_map(rpm: float, throttle: float, temp: float) -> tuple:
                return (throttle, throttle)
        """)
        score = compute_reliability_score(source)
        assert 0.90 <= score <= 1.0

    def test_complex_code_lower_reliability(self):
        source = textwrap.dedent("""
            def engine_map(rpm, throttle, temp):
                if rpm > 10000:
                    if throttle > 0.8:
                        if temp > 100:
                            if rpm > 12000:
                                return (0.5, 0.5)
                            elif rpm > 11000:
                                return (0.7, 0.7)
                            else:
                                return (0.9, 0.9)
                        else:
                            return (throttle, throttle)
                    else:
                        return (throttle * 0.8, throttle * 0.8)
                else:
                    return (1.0, 1.0)
        """)
        score = compute_reliability_score(source)
        assert 0.70 <= score < 0.90

    def test_reliability_clamped(self):
        score = compute_reliability_score("def f():\n    pass\n")
        assert 0.50 <= score <= 1.00
