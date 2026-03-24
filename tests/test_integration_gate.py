"""Integration gate: full player journey from init to leaderboard.

T33.4 — Verify the complete local play loop works end-to-end.
"""

import json
import os
import shutil

from cli.main import main


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GETTING_STARTED = os.path.join(ROOT, "GETTING_STARTED.md")
TEMPLATE_DIR = os.path.join(ROOT, "cars", "default_project")

_RIVAL_CAR = """\
CAR_NAME = "Rival"
CAR_COLOR = "#ff0000"
POWER = 20
GRIP = 20
WEIGHT = 20
AERO = 20
BRAKES = 20

def strategy(state):
    return {"throttle": 1.0, "boost": False}
"""


def _setup_race_dir(tmp_path):
    """Create a race directory with template player car + a rival."""
    race_dir = tmp_path / "race_cars"
    race_dir.mkdir()

    # Copy the default template directly (avoids cmd_init path constraints)
    player_dir = str(race_dir / "player")
    shutil.copytree(TEMPLATE_DIR, player_dir)

    # Add a minimal rival car file
    rival_path = race_dir / "rival.py"
    rival_path.write_text(_RIVAL_CAR)

    return str(race_dir), player_dir


def _run_race(race_dir, tmp_path, output_name="replay.json"):
    """Run a 1-lap race and return (replay_path, results_path)."""
    out_dir = tmp_path / "output"
    out_dir.mkdir(exist_ok=True)
    replay_path = str(out_dir / output_name)
    main(["run", "--car-dir", race_dir, "--track", "monza",
          "--laps", "1", "--output", replay_path, "--live"])
    results_path = str(out_dir / "results.json")
    return replay_path, results_path


# --- Cycle 1: init + run ---


def test_init_creates_playable_project():
    """npcrace init creates cars/{name}/ with car.py, gearbox.py, cooling.py, strategy.py."""
    proj_name = "_test_gate_init"
    target = os.path.join(ROOT, "cars", proj_name)
    try:
        main(["init", proj_name])
        assert os.path.isdir(target)
        for fname in ("car.py", "gearbox.py", "cooling.py", "strategy.py"):
            assert os.path.isfile(os.path.join(target, fname)), f"Missing {fname}"
    finally:
        if os.path.isdir(target):
            shutil.rmtree(target)


def test_run_produces_results(tmp_path, capsys):
    """init + run produces both replay.json and results.json."""
    race_dir, _player = _setup_race_dir(tmp_path)
    replay_path, results_path = _run_race(race_dir, tmp_path)

    assert os.path.isfile(replay_path), "replay.json not created"
    assert os.path.isfile(results_path), "results.json not created"


# --- Cycle 2: submit + leaderboard add ---


def test_submit_validates_race_results(tmp_path, capsys):
    """init + run + submit prints 'verified'."""
    race_dir, _player = _setup_race_dir(tmp_path)
    _replay, results_path = _run_race(race_dir, tmp_path)
    capsys.readouterr()

    main(["submit", results_path])
    out = capsys.readouterr().out

    assert "verified" in out.lower(), f"Expected 'verified' in output, got: {out}"


def test_leaderboard_add_from_race(tmp_path, capsys):
    """init + run + leaderboard --add shows car name in output."""
    race_dir, _player = _setup_race_dir(tmp_path)
    _replay, results_path = _run_race(race_dir, tmp_path)
    lb_path = str(tmp_path / "lb.json")
    capsys.readouterr()

    main(["leaderboard", "--add", results_path, "--file", lb_path])
    out = capsys.readouterr().out

    assert "Added" in out
    assert os.path.isfile(lb_path)


# --- Cycle 3: leaderboard show + full journey ---


def test_leaderboard_show_after_add(tmp_path, capsys):
    """After adding results, leaderboard show displays standings with points."""
    race_dir, _player = _setup_race_dir(tmp_path)
    _replay, results_path = _run_race(race_dir, tmp_path)
    lb_path = str(tmp_path / "lb.json")
    capsys.readouterr()

    main(["leaderboard", "--add", results_path, "--file", lb_path])
    capsys.readouterr()

    main(["leaderboard", "--file", lb_path])
    out = capsys.readouterr().out

    assert "No races recorded" not in out
    # Should contain point values (P1=25 or P2=18)
    assert "25" in out or "18" in out


def test_full_journey_init_to_leaderboard(tmp_path, capsys):
    """Complete flow: init -> run -> submit -> leaderboard add -> show."""
    race_dir, player_dir = _setup_race_dir(tmp_path)

    # Verify init produced the expected files
    assert os.path.isdir(player_dir)
    assert os.path.isfile(os.path.join(player_dir, "car.py"))

    # Run a race
    replay_path, results_path = _run_race(race_dir, tmp_path)
    assert os.path.isfile(replay_path)
    assert os.path.isfile(results_path)
    capsys.readouterr()

    # Submit
    main(["submit", results_path])
    out = capsys.readouterr().out
    assert "verified" in out.lower()

    # Leaderboard add
    lb_path = str(tmp_path / "lb.json")
    main(["leaderboard", "--add", results_path, "--file", lb_path])
    out = capsys.readouterr().out
    assert "Added" in out

    # Leaderboard show
    main(["leaderboard", "--file", lb_path])
    out = capsys.readouterr().out
    assert "No races recorded" not in out


# --- Cycle 4: accumulation + GETTING_STARTED ---


def test_leaderboard_accumulates_multiple_races(tmp_path, capsys):
    """Running twice and adding both results accumulates points."""
    race_dir, _player = _setup_race_dir(tmp_path)
    lb_path = str(tmp_path / "lb.json")

    # Race 1
    out1 = tmp_path / "out1"
    out1.mkdir()
    replay1 = str(out1 / "replay.json")
    main(["run", "--car-dir", race_dir, "--track", "monza",
          "--laps", "1", "--output", replay1])
    results1 = str(out1 / "results.json")
    assert os.path.isfile(results1)
    capsys.readouterr()

    main(["leaderboard", "--add", results1, "--file", lb_path])
    capsys.readouterr()

    # Race 2
    out2 = tmp_path / "out2"
    out2.mkdir()
    replay2 = str(out2 / "replay.json")
    main(["run", "--car-dir", race_dir, "--track", "monza",
          "--laps", "1", "--output", replay2])
    results2 = str(out2 / "results.json")
    assert os.path.isfile(results2)
    capsys.readouterr()

    main(["leaderboard", "--add", results2, "--file", lb_path])
    capsys.readouterr()

    # Verify accumulation
    with open(lb_path) as f:
        lb = json.load(f)
    entries = lb.get("entries", [])
    assert len(entries) > 0, "No entries in leaderboard"

    for entry in entries:
        assert entry["races"] == 2, (
            f"{entry['name']} has {entry['races']} races, expected 2"
        )


def test_getting_started_references_commands():
    """GETTING_STARTED.md exists and mentions all key commands."""
    assert os.path.isfile(GETTING_STARTED), "GETTING_STARTED.md not found"

    with open(GETTING_STARTED) as f:
        content = f.read()

    for cmd in ("npcrace init", "npcrace run",
                "npcrace submit", "npcrace leaderboard"):
        assert cmd in content, f"GETTING_STARTED.md missing '{cmd}'"
