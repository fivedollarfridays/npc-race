"""Tests for the 'npcrace submit' CLI command."""

import json

from engine.results import generate_results_summary


def _make_valid_results(tmp_path):
    """Create a valid results.json file and return its path."""
    replay = {
        "track_name": "monza",
        "laps": 5,
        "results": [
            {
                "name": "CarA",
                "position": 1,
                "total_time_s": 405.23,
                "best_lap_s": 80.12,
                "lap_times": [81.5, 80.8, 80.3, 80.12, 82.5],
                "finished": True,
            },
            {
                "name": "CarB",
                "position": 2,
                "total_time_s": 408.50,
                "best_lap_s": 81.00,
                "lap_times": [82.0, 81.5, 81.0, 81.5, 82.5],
                "finished": True,
            },
        ],
    }
    cars = [
        {"CAR_NAME": "CarA", "_loaded_parts": ["gearbox"], "reliability_score": 0.94},
        {"CAR_NAME": "CarB", "_loaded_parts": [], "reliability_score": 1.0},
    ]
    summary = generate_results_summary(replay, cars, league="F3")
    path = tmp_path / "results.json"
    path.write_text(json.dumps(summary))
    return str(path), summary


# --- Test 1: argparse accepts submit ---

def test_cli_has_submit_command():
    """The CLI parser accepts 'submit' as a valid subcommand."""
    from cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["submit", "results.json"])
    assert args.command == "submit"
    assert args.results_file == "results.json"


# --- Test 2: missing file ---

def test_submit_missing_file(capsys):
    """Submit with a nonexistent file prints an error and returns 1."""
    from cli.commands import cmd_submit

    class Args:
        results_file = "/no/such/file.json"

    rc = cmd_submit(Args())
    assert rc == 1
    out = capsys.readouterr().out
    assert "Error" in out
    assert "not found" in out.lower() or "File not found" in out


# --- Test 3: invalid JSON ---

def test_submit_invalid_json(tmp_path, capsys):
    """Submit with a non-JSON file prints an error and returns 1."""
    from cli.commands import cmd_submit

    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{")

    class Args:
        results_file = str(bad)

    rc = cmd_submit(Args())
    assert rc == 1
    out = capsys.readouterr().out
    assert "Invalid JSON" in out


# --- Test 4: valid results ---

def test_submit_valid_results(tmp_path):
    """Submit a valid results file returns exit code 0."""
    from cli.commands import cmd_submit

    path, _ = _make_valid_results(tmp_path)

    class Args:
        results_file = path

    rc = cmd_submit(Args())
    assert rc == 0


# --- Test 5: tampered results ---

def test_submit_tampered_results(tmp_path, capsys):
    """Submit tampered results returns exit code 1."""
    from cli.commands import cmd_submit

    path, summary = _make_valid_results(tmp_path)
    # Tamper with a field
    summary["cars"][0]["total_time_s"] = 999.99
    with open(path, "w") as f:
        json.dump(summary, f)

    class Args:
        results_file = path

    rc = cmd_submit(Args())
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAILED" in out


# --- Test 6: prints summary ---

def test_submit_prints_summary(tmp_path, capsys):
    """Submit prints track, laps, and car positions."""
    from cli.commands import cmd_submit

    path, _ = _make_valid_results(tmp_path)

    class Args:
        results_file = path

    cmd_submit(Args())
    out = capsys.readouterr().out
    assert "monza" in out.lower()
    assert "Laps: 5" in out
    assert "P1" in out
    assert "P2" in out
    assert "CarA" in out
    assert "CarB" in out
    assert "sha256:" in out
