"""Tests for security.bot_scanner — static analysis of car files."""

import os
import textwrap

import pytest

from security.bot_scanner import ALLOWED_IMPORTS, ScanResult, scan_car_file, scan_car_source


CARS_DIR = os.path.join(os.path.dirname(__file__), "..", "cars")


# --- ScanResult basics ---


class TestScanResult:
    def test_passed_when_no_violations(self):
        r = ScanResult(passed=True, violations=[])
        assert r.passed is True
        assert r.violations == []

    def test_failed_when_violations(self):
        r = ScanResult(passed=False, violations=["bad import"])
        assert r.passed is False
        assert "bad import" in r.violations


# --- Syntax errors ---


class TestSyntaxErrors:
    def test_syntax_error_fails(self):
        result = scan_car_source("def strategy(:\n")
        assert result.passed is False
        assert any("Syntax error" in v for v in result.violations)


# --- ALLOWLIST imports ---


class TestImportAllowlist:
    def test_allowed_import_passes(self):
        src = textwrap.dedent("""\
            import math
            import random
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is True

    def test_disallowed_import_os(self):
        src = textwrap.dedent("""\
            import os
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("os" in v for v in result.violations)

    def test_disallowed_from_import(self):
        src = textwrap.dedent("""\
            from subprocess import run
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("subprocess" in v for v in result.violations)

    def test_allowed_from_import(self):
        src = textwrap.dedent("""\
            from collections import defaultdict
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is True

    def test_allowed_imports_set(self):
        assert ALLOWED_IMPORTS == {"math", "random", "collections", "itertools", "functools", "json"}


# --- Blocked calls ---


class TestBlockedCalls:
    def test_eval_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                eval("1+1")
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("eval" in v for v in result.violations)

    def test_exec_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                exec("pass")
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("exec" in v for v in result.violations)

    def test_open_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                open("/etc/passwd")
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v for v in result.violations)

    def test_getattr_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                getattr(state, "x")
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("getattr" in v for v in result.violations)


# --- Blocked dunder attrs ---


class TestBlockedDunderAttrs:
    def test_globals_dunder_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                x = state.__globals__
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("__globals__" in v for v in result.violations)

    def test_builtins_dunder_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                x = state.__builtins__
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("__builtins__" in v for v in result.violations)

    def test_subclasses_dunder_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                x = ().__class__.__subclasses__()
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("__subclasses__" in v for v in result.violations)


# --- Module-level code ---


class TestModuleLevelCode:
    def test_bare_function_call_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            print("hello")
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("top-level" in v.lower() or "module" in v.lower() for v in result.violations)

    def test_docstring_allowed(self):
        src = textwrap.dedent('''\
            """This is a docstring."""
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        ''')
        result = scan_car_source(src)
        assert result.passed is True

    def test_if_name_main_allowed(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
            if __name__ == "__main__":
                pass
        """)
        result = scan_car_source(src)
        assert result.passed is True


# --- Semicolons in strategy ---


class TestSemicolons:
    def test_semicolon_in_strategy_blocked(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                x = 1; y = 2
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("semicolon" in v.lower() for v in result.violations)

    def test_semicolon_in_string_ok(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                x = "hello; world"
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is True


# --- Car-specific validation ---


class TestCarValidation:
    def test_missing_car_name(self):
        src = textwrap.dedent("""\
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("CAR_NAME" in v for v in result.violations)

    def test_empty_car_name(self):
        src = textwrap.dedent("""\
            CAR_NAME = ""
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("CAR_NAME" in v for v in result.violations)

    def test_invalid_hex_color(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "red"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("CAR_COLOR" in v for v in result.violations)

    def test_missing_stat(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("BRAKES" in v for v in result.violations)

    def test_negative_stat(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = -5
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("negative" in v.lower() or "POWER" in v for v in result.violations)

    def test_non_numeric_stat(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = "fast"
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("numeric" in v.lower() or "POWER" in v for v in result.violations)

    def test_budget_over_100(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 30
            GRIP = 30
            WEIGHT = 30
            AERO = 30
            BRAKES = 30
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is False
        assert any("budget" in v.lower() for v in result.violations)

    def test_budget_exactly_100_passes(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is True

    def test_float_stats_allowed(self):
        src = textwrap.dedent("""\
            CAR_NAME = "Test"
            CAR_COLOR = "#aabbcc"
            POWER = 20.5
            GRIP = 19.5
            WEIGHT = 20.0
            AERO = 20.0
            BRAKES = 20.0
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """)
        result = scan_car_source(src)
        assert result.passed is True


# --- scan_car_file ---


class TestScanCarFile:
    def test_nonexistent_file(self):
        result = scan_car_file("/nonexistent/path.py")
        assert result.passed is False
        assert any("read" in v.lower() or "file" in v.lower() for v in result.violations)

    def test_valid_car_file(self, tmp_path):
        car = tmp_path / "good_car.py"
        car.write_text(textwrap.dedent("""\
            CAR_NAME = "Good"
            CAR_COLOR = "#112233"
            POWER = 20
            GRIP = 20
            WEIGHT = 20
            AERO = 20
            BRAKES = 20
            def strategy(state):
                return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
        """))
        result = scan_car_file(str(car))
        assert result.passed is True


# --- Seed cars pass ---


class TestSeedCars:
    @pytest.mark.parametrize("filename", [
        "brickhouse.py", "glasscanon.py", "gooseloose.py",
        "silky.py", "slipstream.py",
    ])
    def test_seed_car_passes(self, filename):
        path = os.path.join(CARS_DIR, filename)
        assert os.path.exists(path), f"Seed car not found: {path}"
        result = scan_car_file(path)
        assert result.passed is True, f"{filename} failed: {result.violations}"
