"""Tests for bot_scanner v3 — deep import scanner for car projects."""

import os
import textwrap

from security.bot_scanner import scan_car_project, ScanResult


def _write_file(base, relpath, content):
    """Write a Python file at base/relpath with dedented content."""
    full = os.path.join(base, relpath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(textwrap.dedent(content))


class TestCleanProject:
    def test_single_clean_file_passes(self, tmp_path):
        _write_file(tmp_path, "car.py", """\
            import math
            x = math.sqrt(4)
        """)
        result = scan_car_project(str(tmp_path))
        assert result.passed is True, f"Violations: {result.violations}"

    def test_clean_project_with_helper(self, tmp_path):
        _write_file(tmp_path, "car.py", """\
            from helpers import utils
        """)
        _write_file(tmp_path, "helpers/__init__.py", "")
        _write_file(tmp_path, "helpers/utils.py", """\
            import math
            def double(x):
                return x * 2
        """)
        result = scan_car_project(str(tmp_path))
        assert result.passed is True, f"Violations: {result.violations}"


class TestForbiddenImportAtDepth:
    def test_forbidden_import_in_helper_caught(self, tmp_path):
        _write_file(tmp_path, "car.py", """\
            from helpers import utils
        """)
        _write_file(tmp_path, "helpers/__init__.py", "")
        _write_file(tmp_path, "helpers/utils.py", """\
            import os
            def read_file(path):
                return os.path.exists(path)
        """)
        result = scan_car_project(str(tmp_path))
        assert result.passed is False
        assert any("os" in v for v in result.violations)

    def test_violation_includes_chain_path(self, tmp_path):
        _write_file(tmp_path, "car.py", """\
            from helpers import utils
        """)
        _write_file(tmp_path, "helpers/__init__.py", "")
        _write_file(tmp_path, "helpers/utils.py", """\
            import subprocess
        """)
        result = scan_car_project(str(tmp_path))
        assert result.passed is False
        # Should mention the file path where violation occurred
        violation_text = " ".join(result.violations)
        assert "helpers" in violation_text


class TestRelativeImports:
    def test_relative_import_within_project_allowed(self, tmp_path):
        _write_file(tmp_path, "pkg/__init__.py", "")
        _write_file(tmp_path, "pkg/main.py", """\
            from . import helper
        """)
        _write_file(tmp_path, "pkg/helper.py", """\
            import math
            val = math.pi
        """)
        result = scan_car_project(str(tmp_path))
        assert result.passed is True, f"Violations: {result.violations}"


class TestStdlibImports:
    def test_stdlib_allowed_in_all_files(self, tmp_path):
        _write_file(tmp_path, "car.py", """\
            import math
            import random
        """)
        _write_file(tmp_path, "helpers.py", """\
            import itertools
            import functools
        """)
        result = scan_car_project(str(tmp_path))
        assert result.passed is True, f"Violations: {result.violations}"


class TestCircularImports:
    def test_circular_imports_dont_hang(self, tmp_path):
        _write_file(tmp_path, "a.py", """\
            from b import something
            val = 1
        """)
        _write_file(tmp_path, "b.py", """\
            from a import val
            something = 2
        """)
        # Should complete without hanging, regardless of pass/fail
        result = scan_car_project(str(tmp_path))
        assert isinstance(result, ScanResult)


class TestMissingImportedFile:
    def test_missing_module_reported(self, tmp_path):
        _write_file(tmp_path, "car.py", """\
            from helpers import utils
        """)
        # helpers/utils.py does NOT exist
        result = scan_car_project(str(tmp_path))
        assert result.passed is False
        violation_text = " ".join(result.violations)
        assert "not found" in violation_text.lower() or "missing" in violation_text.lower()
