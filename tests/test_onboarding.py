"""Tests for onboarding: GETTING_STARTED.md and npcrace init polish."""

import os
import shutil
import types


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GETTING_STARTED = os.path.join(ROOT, "GETTING_STARTED.md")
CARS_DIR = os.path.join(ROOT, "cars")


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


def test_init_creates_project_inside_cars():
    """npcrace init my_car creates cars/my_car/ with template files."""
    name = "_test_init_onboarding"
    target = os.path.join(CARS_DIR, name)
    try:
        args = _make_init_args(name)
        from cli.commands import cmd_init

        result = cmd_init(args)
        assert result == 0
        assert os.path.isdir(target)
        assert os.path.isfile(os.path.join(target, "car.py"))
        assert os.path.isfile(os.path.join(target, "gearbox.py"))
        assert os.path.isfile(os.path.join(target, "cooling.py"))
        assert os.path.isfile(os.path.join(target, "strategy.py"))
    finally:
        if os.path.isdir(target):
            shutil.rmtree(target)


def test_init_sets_car_name_pascal_case():
    """npcrace init my_car sets CAR_NAME = 'MyCar' in car.py."""
    name = "_test_init_pascal"
    target = os.path.join(CARS_DIR, name)
    try:
        from cli.commands import cmd_init

        cmd_init(_make_init_args(name))
        car_py = os.path.join(target, "car.py")
        with open(car_py) as f:
            content = f.read()
        assert 'CAR_NAME = "TestInitPascal"' in content
    finally:
        if os.path.isdir(target):
            shutil.rmtree(target)


def test_init_rejects_absolute_path():
    """npcrace init /tmp/foo returns error code 1."""
    from cli.commands import cmd_init

    result = cmd_init(_make_init_args("/tmp/foo"))
    assert result == 1


def test_init_rejects_path_with_separator():
    """npcrace init some/nested returns error code 1."""
    from cli.commands import cmd_init

    result = cmd_init(_make_init_args("some/nested"))
    assert result == 1


def test_init_existing_dir_fails():
    """init to existing dir returns error code 1."""
    name = "_test_init_exists"
    target = os.path.join(CARS_DIR, name)
    try:
        os.makedirs(target, exist_ok=True)
        from cli.commands import cmd_init

        result = cmd_init(_make_init_args(name))
        assert result == 1
    finally:
        if os.path.isdir(target):
            shutil.rmtree(target)


def test_init_project_has_readme():
    """Created project contains README.md."""
    name = "_test_init_readme"
    target = os.path.join(CARS_DIR, name)
    try:
        from cli.commands import cmd_init

        cmd_init(_make_init_args(name))
        assert os.path.isfile(os.path.join(target, "README.md"))
    finally:
        if os.path.isdir(target):
            shutil.rmtree(target)


# --- helpers ---


def _read_getting_started() -> str:
    with open(GETTING_STARTED) as f:
        return f.read()


def _make_init_args(name: str):
    """Create a namespace that looks like parsed init args."""
    return types.SimpleNamespace(dir=name)
