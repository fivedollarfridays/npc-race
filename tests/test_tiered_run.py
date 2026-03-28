"""Tests for tiered run: --tier and --full-grid CLI flags + tier wiring."""

import json
from unittest.mock import patch

import pytest

from cli.main import _build_parser


# --- Cycle 1: Parser flags ---


def test_run_parser_accepts_tier_flag():
    """--tier flag is accepted with valid choices."""
    parser = _build_parser()
    args = parser.parse_args(["run", "--tier", "rookie"])
    assert args.tier == "rookie"


def test_run_parser_tier_choices():
    """--tier only accepts rookie, midfield, front, full."""
    parser = _build_parser()
    for valid in ("rookie", "midfield", "front", "full"):
        args = parser.parse_args(["run", "--tier", valid])
        assert args.tier == valid

    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--tier", "legendary"])


def test_run_parser_tier_default_is_none():
    """Without --tier, default is None (so progression file determines it)."""
    parser = _build_parser()
    args = parser.parse_args(["run"])
    assert args.tier is None


def test_run_parser_accepts_full_grid_flag():
    """--full-grid flag is a boolean store_true."""
    parser = _build_parser()
    args = parser.parse_args(["run", "--full-grid"])
    assert args.full_grid is True


def test_run_parser_full_grid_default_false():
    """Without --full-grid, default is False."""
    parser = _build_parser()
    args = parser.parse_args(["run"])
    assert args.full_grid is False


# --- Cycle 2: _get_player_tier helper ---


def test_get_player_tier_default_rookie(tmp_path):
    """No progress file means rookie."""
    from cli.commands import _get_player_tier

    fake_path = str(tmp_path / "progress.json")
    assert _get_player_tier(fake_path) == "rookie"


def test_get_player_tier_reads_file(tmp_path):
    """Reads tier from progress.json."""
    from cli.commands import _get_player_tier

    prog_file = tmp_path / "progress.json"
    prog_file.write_text(json.dumps({"tier": "midfield"}))
    assert _get_player_tier(str(prog_file)) == "midfield"


def test_get_player_tier_missing_tier_key(tmp_path):
    """Progress file exists but has no 'tier' key -> rookie."""
    from cli.commands import _get_player_tier

    prog_file = tmp_path / "progress.json"
    prog_file.write_text(json.dumps({"xp": 100}))
    assert _get_player_tier(str(prog_file)) == "rookie"


# --- Cycle 3: cmd_run wires tier to run_race ---


def test_cmd_run_passes_tier_to_run_race(tmp_path):
    """--tier rookie should pass tier='rookie' to run_race."""
    car_dir = tmp_path / "cars"
    car_dir.mkdir()

    parser = _build_parser()
    args = parser.parse_args(["run", "--car-dir", str(car_dir), "--tier", "rookie"])

    with patch("cli.commands.run_race") as mock_run:
        from cli.commands import cmd_run
        cmd_run(args)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["tier"] == "rookie"


def test_cmd_run_full_grid_sets_tier_full(tmp_path):
    """--full-grid should pass tier='full' to run_race."""
    car_dir = tmp_path / "cars"
    car_dir.mkdir()

    parser = _build_parser()
    args = parser.parse_args(["run", "--car-dir", str(car_dir), "--full-grid"])

    with patch("cli.commands.run_race") as mock_run:
        from cli.commands import cmd_run
        cmd_run(args)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["tier"] == "full"


def test_cmd_run_default_tier_from_progression(tmp_path):
    """No --tier/--full-grid reads progression (default rookie)."""
    car_dir = tmp_path / "cars"
    car_dir.mkdir()

    parser = _build_parser()
    args = parser.parse_args(["run", "--car-dir", str(car_dir)])

    with (
        patch("cli.commands.run_race") as mock_run,
        patch("cli.commands._get_player_tier", return_value="midfield"),
    ):
        from cli.commands import cmd_run
        cmd_run(args)
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["tier"] == "midfield"


# --- Cycle 4: run_race uses load_tier_cars when tier is set ---


def _make_fake_cars(names):
    """Create minimal car dicts for testing."""
    return [{"CAR_NAME": n, "parts": {}} for n in names]


ROOKIE_NAMES = ["Tortoise", "RustBucket", "PaperWeight", "SteamRoller"]


def test_load_and_filter_uses_tier_cars_for_rookie():
    """_load_and_filter_cars with tier='rookie' uses load_tier_cars."""
    from engine.race_runner import _load_and_filter_cars

    fake_rookie = _make_fake_cars(ROOKIE_NAMES)

    with (
        patch("engine.race_runner.load_all_cars") as mock_all,
        patch("engine.tiers.load_all_cars", return_value=fake_rookie),
        patch("engine.race_runner.apply_league_gates",
              side_effect=lambda cars, lg, **kw: (cars, lg or "F3")),
    ):
        cars, _ = _load_and_filter_cars("cars", None, None, tier="rookie")
        mock_all.assert_not_called()
        assert len(cars) == 4


def test_load_and_filter_uses_all_cars_for_full():
    """_load_and_filter_cars with tier='full' uses load_all_cars."""
    from engine.race_runner import _load_and_filter_cars

    fake_all = _make_fake_cars([f"Car{i}" for i in range(19)])

    with (
        patch("engine.race_runner.load_all_cars", return_value=fake_all),
        patch("engine.race_runner.apply_league_gates",
              side_effect=lambda cars, lg, **kw: (cars, lg or "F3")),
    ):
        cars, _ = _load_and_filter_cars("cars", None, None, tier="full")
        assert len(cars) == 19


def test_load_and_filter_uses_all_cars_when_no_tier():
    """_load_and_filter_cars with tier=None uses load_all_cars."""
    from engine.race_runner import _load_and_filter_cars

    fake_all = _make_fake_cars([f"Car{i}" for i in range(19)])

    with (
        patch("engine.race_runner.load_all_cars", return_value=fake_all),
        patch("engine.race_runner.apply_league_gates",
              side_effect=lambda cars, lg, **kw: (cars, lg or "F3")),
    ):
        cars, _ = _load_and_filter_cars("cars", None, None, tier=None)
        assert len(cars) == 19
