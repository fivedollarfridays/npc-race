"""Tests for the npcrace trial CLI command."""

import os

import pytest

pytest.importorskip("engine.time_trial")


def test_trial_command_exists():
    """trial subcommand is registered in the CLI parser."""
    from cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["trial", "--track", "monza"])
    assert args.command == "trial"


def test_trial_default_track():
    """Default track is monza when --track is omitted."""
    from cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["trial"])
    assert args.track == "monza"


def test_trial_invalid_track(capsys):
    """Invalid track name exits with error code 1."""
    import types

    from cli.trial_command import cmd_trial

    args = types.SimpleNamespace(track="fakecircuit", car_dir="cars/default_project")
    result = cmd_trial(args)
    assert result == 1
    out = capsys.readouterr().out
    assert "Unknown track" in out or "unknown" in out.lower()


def test_trial_missing_car_dir(capsys):
    """Non-existent car dir exits with error code 1."""
    import types

    from cli.trial_command import cmd_trial

    args = types.SimpleNamespace(track="monza", car_dir="/nonexistent_dir_xyz")
    result = cmd_trial(args)
    assert result == 1
    out = capsys.readouterr().out
    assert "not found" in out.lower() or "error" in out.lower()


@pytest.mark.smoke
def test_trial_runs_and_shows_output(tmp_path, capsys):
    """trial command runs a full trial and shows efficiency breakdown."""
    import shutil
    import types

    from cli.trial_command import cmd_trial

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template = os.path.join(repo_root, "cars", "default_project")
    car_dir = str(tmp_path / "test_car")
    shutil.copytree(template, car_dir)

    args = types.SimpleNamespace(track="monza", car_dir=car_dir)
    result = cmd_trial(args)

    assert result == 0
    out = capsys.readouterr().out
    assert "TIME TRIAL" in out
    assert "MONZA" in out
    assert "Lap time:" in out
    assert "EFFICIENCY" in out
