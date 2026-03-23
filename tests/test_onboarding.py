"""Tests for onboarding: GETTING_STARTED.md and npcrace init polish."""

import os
import types


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GETTING_STARTED = os.path.join(ROOT, "GETTING_STARTED.md")


# --- GETTING_STARTED.md tests ---


def test_getting_started_exists():
    """GETTING_STARTED.md exists at repo root."""
    assert os.path.isfile(GETTING_STARTED), "GETTING_STARTED.md not found at repo root"


def test_getting_started_has_quick_start():
    """Contains npcrace init and npcrace run commands."""
    content = _read_getting_started()
    assert "npcrace init" in content
    assert "npcrace run" in content


def test_getting_started_has_before_after():
    """Contains the gearbox improvement example with before/after."""
    content = _read_getting_started()
    assert "12800" in content or "12,800" in content, "Missing default shift RPM"
    assert "12200" in content or "12,200" in content, "Missing improved shift RPM"


# --- npcrace init tests ---


def test_init_creates_project(tmp_path):
    """npcrace init creates directory with car.py + 3 part files."""
    target = str(tmp_path / "my_car")
    args = _make_init_args(target)

    from cli.commands import cmd_init

    result = cmd_init(args)
    assert result == 0
    assert os.path.isdir(target)
    assert os.path.isfile(os.path.join(target, "car.py"))
    assert os.path.isfile(os.path.join(target, "gearbox.py"))
    assert os.path.isfile(os.path.join(target, "cooling.py"))
    assert os.path.isfile(os.path.join(target, "strategy.py"))


def test_init_existing_dir_fails(tmp_path):
    """init to existing dir returns error code 1."""
    target = str(tmp_path / "my_car")
    os.makedirs(target)

    from cli.commands import cmd_init

    args = _make_init_args(target)
    result = cmd_init(args)
    assert result == 1


def test_init_project_has_readme(tmp_path):
    """Created project contains README.md."""
    target = str(tmp_path / "my_car")
    args = _make_init_args(target)

    from cli.commands import cmd_init

    cmd_init(args)
    assert os.path.isfile(os.path.join(target, "README.md"))


# --- helpers ---


def _read_getting_started() -> str:
    with open(GETTING_STARTED) as f:
        return f.read()


def _make_init_args(target: str):
    """Create a namespace that looks like parsed init args."""
    return types.SimpleNamespace(dir=target)
