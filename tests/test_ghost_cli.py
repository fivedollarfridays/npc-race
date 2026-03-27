"""Tests for ghost race CLI command."""

import os
import shutil
import types

import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CAR = os.path.join(REPO_ROOT, "cars", "default_project")


def _parse_ghost(argv: list[str]):
    """Parse ghost subcommand args via the real CLI parser."""
    from cli.main import _build_parser

    parser = _build_parser()
    return parser.parse_args(["ghost"] + argv)


def test_ghost_command_exists():
    """Parser accepts 'ghost' subcommand without error."""
    args = _parse_ghost([])
    assert args.command == "ghost"


def test_ghost_default_level():
    """Default level is 1."""
    args = _parse_ghost([])
    assert args.level == 1


def test_ghost_default_track():
    """Default track is monza."""
    args = _parse_ghost([])
    assert args.track == "monza"


def test_ghost_invalid_level(capsys):
    """Level 0 returns exit code 1."""
    from cli.ghost_command import cmd_ghost

    args = types.SimpleNamespace(
        track="monza", level=0, car_dir=DEFAULT_CAR,
    )
    rc = cmd_ghost(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Level must be 1-5" in out


def test_ghost_invalid_track(capsys):
    """Fake track returns exit code 1."""
    from cli.ghost_command import cmd_ghost

    args = types.SimpleNamespace(
        track="atlantis", level=1, car_dir=DEFAULT_CAR,
    )
    rc = cmd_ghost(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Unknown track" in out


def test_ghost_no_car(capsys):
    """Missing car dir returns exit code 1."""
    from cli.ghost_command import cmd_ghost

    args = types.SimpleNamespace(
        track="monza", level=1, car_dir="/tmp/no_such_car_dir_xyz",
    )
    rc = cmd_ghost(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "Car directory not found" in out


@pytest.mark.smoke
def test_ghost_runs(tmp_path, capsys):
    """Level 1 ghost race runs end-to-end, output contains GHOST RACE."""
    from cli.ghost_command import cmd_ghost

    if not os.path.isdir(DEFAULT_CAR):
        pytest.skip("default_project not found")

    car_dir = str(tmp_path / "test_car")
    shutil.copytree(DEFAULT_CAR, car_dir)

    args = types.SimpleNamespace(
        track="monza", level=1, car_dir=car_dir,
    )
    rc = cmd_ghost(args)
    assert rc == 0

    out = capsys.readouterr().out
    assert "GHOST RACE" in out
    assert "Level 1" in out
