"""Tests for the leaderboard CLI subcommand."""

import json

from cli.main import _build_parser, main
from engine.results import generate_results_summary


def _make_valid_results(tmp_path, track="monza", num_cars=3):
    """Create a valid results file with integrity hash."""
    replay = {
        "track_name": track,
        "laps": 5,
        "results": [
            {"name": f"Car_{i}", "position": i, "total_time_s": 80.0 + i,
             "best_lap_s": 15.0 + i * 0.5, "lap_times": [16.0 + i] * 5,
             "finished": True}
            for i in range(1, num_cars + 1)
        ],
    }
    cars = [{"CAR_NAME": f"Car_{i}"} for i in range(1, num_cars + 1)]
    summary = generate_results_summary(replay, cars, league="F3")

    path = tmp_path / "results.json"
    with open(path, "w") as f:
        json.dump(summary, f)
    return str(path), summary


# --- Cycle 1: parser + empty leaderboard ---


def test_cli_has_leaderboard_command():
    """Argparse accepts 'leaderboard' as a valid subcommand."""
    parser = _build_parser()
    args = parser.parse_args(["leaderboard"])
    assert args.command == "leaderboard"


def test_leaderboard_empty(tmp_path, capsys):
    """No races recorded shows empty message."""
    lb_path = str(tmp_path / "lb.json")
    main(["leaderboard", "--file", lb_path])
    out = capsys.readouterr().out
    assert "No races recorded yet." in out


# --- Cycle 2: add results + missing file ---


def test_leaderboard_add_results(tmp_path, capsys):
    """Adding valid results shows cars in standings."""
    results_path, _ = _make_valid_results(tmp_path)
    lb_path = str(tmp_path / "lb.json")

    main(["leaderboard", "--add", results_path, "--file", lb_path])
    out = capsys.readouterr().out

    assert "Added 3 cars" in out
    assert "Car_1" in out
    assert "Car_2" in out


def test_leaderboard_missing_file(tmp_path, capsys):
    """--add with nonexistent file prints error and exits non-zero."""
    import pytest
    lb_path = str(tmp_path / "lb.json")
    with pytest.raises(SystemExit) as exc:
        main(["leaderboard", "--add", "/no/such/file.json", "--file", lb_path])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Error" in out or "not found" in out


# --- Cycle 3: invalid results, reset, accumulates ---


def test_leaderboard_add_invalid_results(tmp_path, capsys):
    """Tampered results are rejected."""
    results_path, _ = _make_valid_results(tmp_path)

    # Tamper with the file
    with open(results_path) as f:
        data = json.load(f)
    data["cars"][0]["position"] = 99
    with open(results_path, "w") as f:
        json.dump(data, f)

    import pytest
    lb_path = str(tmp_path / "lb.json")
    with pytest.raises(SystemExit) as exc:
        main(["leaderboard", "--add", results_path, "--file", lb_path])
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "integrity" in out.lower()


def test_leaderboard_reset(tmp_path, capsys):
    """--reset clears all standings."""
    results_path, _ = _make_valid_results(tmp_path)
    lb_path = str(tmp_path / "lb.json")

    # Add results first
    main(["leaderboard", "--add", results_path, "--file", lb_path])
    capsys.readouterr()  # clear

    # Reset
    main(["leaderboard", "--reset", "--file", lb_path])
    out = capsys.readouterr().out
    assert "reset" in out.lower()

    # Verify empty
    main(["leaderboard", "--file", lb_path])
    out = capsys.readouterr().out
    assert "No races recorded yet." in out


def test_leaderboard_accumulates(tmp_path, capsys):
    """Adding results twice accumulates races and points."""
    results_path, _ = _make_valid_results(tmp_path, num_cars=2)
    lb_path = str(tmp_path / "lb.json")

    main(["leaderboard", "--add", results_path, "--file", lb_path])
    capsys.readouterr()

    # Add again (same results file)
    main(["leaderboard", "--add", results_path, "--file", lb_path])
    out = capsys.readouterr().out

    # Should show standings with accumulated data
    assert "Car_1" in out
    # Car_1 is P1 both times: 25 + 25 = 50
    assert "50" in out
