"""Tests for T38.4 polish fixes (Bugs #11-16)."""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Bug 11: "1 laps" grammar
# ---------------------------------------------------------------------------

def test_singular_lap_in_dashboard():
    """Dashboard should say '1 lap' not '1 laps'."""
    from engine.race_dashboard import generate_dashboard

    results = [
        {"position": 1, "name": "TestCar", "finished": True,
         "total_time_s": 90.0, "best_lap_s": 90.0, "pit_stops": 0},
    ]
    output = generate_dashboard(results, track_name="monza", laps=1)
    assert "(1 lap)" in output
    assert "(1 laps)" not in output


def test_plural_laps_in_dashboard():
    """Dashboard should still say '5 laps' for plural."""
    from engine.race_dashboard import generate_dashboard

    results = [
        {"position": 1, "name": "TestCar", "finished": True,
         "total_time_s": 450.0, "best_lap_s": 88.5, "pit_stops": 0},
    ]
    output = generate_dashboard(results, track_name="monza", laps=5)
    assert "(5 laps)" in output


# ---------------------------------------------------------------------------
# Bug 12: No lap chart for short races
# ---------------------------------------------------------------------------

def test_no_lap_chart_for_short_races():
    """Lap chart section should be skipped when laps < 5."""
    from engine.race_dashboard import generate_dashboard

    results = [
        {"position": 1, "name": "TestCar", "finished": True,
         "total_time_s": 270.0, "best_lap_s": 88.0, "pit_stops": 0},
    ]
    lap_summaries = {
        "TestCar": [
            {"lap": i, "position": 1, "tire_compound": "soft"}
            for i in range(1, 4)
        ],
    }
    output = generate_dashboard(
        results, lap_summaries=lap_summaries, track_name="monza", laps=3,
    )
    assert "LAP CHART" not in output


def test_lap_chart_shown_for_long_races():
    """Lap chart should still appear when laps >= 5."""
    from engine.race_dashboard import generate_dashboard

    results = [
        {"position": 1, "name": "TestCar", "finished": True,
         "total_time_s": 450.0, "best_lap_s": 88.0, "pit_stops": 0},
    ]
    lap_summaries = {
        "TestCar": [
            {"lap": i, "position": 1, "tire_compound": "soft"}
            for i in range(1, 11)
        ],
    }
    output = generate_dashboard(
        results, lap_summaries=lap_summaries, track_name="monza", laps=10,
    )
    assert "LAP CHART" in output


# ---------------------------------------------------------------------------
# Bug 13: Wizard stub in help
# ---------------------------------------------------------------------------

def test_no_wizard_in_help():
    """The wizard subcommand should not appear in CLI parser."""
    from cli.main import _build_parser

    parser = _build_parser()
    # Check that wizard is not a registered subcommand
    for action in parser._subparsers._actions:
        if hasattr(action, "_parser_class"):
            assert "wizard" not in action.choices, (
                "wizard subcommand should be removed"
            )


# ---------------------------------------------------------------------------
# Bug 14: run vs race help text
# ---------------------------------------------------------------------------

def test_help_distinguishes_run_race():
    """run and race subcommands should have distinct help strings."""
    from cli.main import _build_parser

    parser = _build_parser()
    # Check via the parser help strings stored at registration time
    for action in parser._subparsers._actions:
        if hasattr(action, "_parser_class"):
            choices_actions = action._choices_actions
            helps = {a.dest: a.help for a in choices_actions}
            assert "run" in helps
            assert "race" in helps
            assert "fast mode" in helps["run"].lower()
            assert "weekend" in helps["race"].lower() or "qualifying" in helps["race"].lower()


# ---------------------------------------------------------------------------
# Bug 15: Template README wrong command
# ---------------------------------------------------------------------------

def test_template_readme_correct_command():
    """Template README should use the npcrace CLI, not python -m."""
    readme_path = "/home/kmasty/projects/npc-race/cars/default_project/README.md"
    with open(readme_path) as f:
        content = f.read()
    assert "python -m npc_race" not in content
    assert "npcrace run" in content


# ---------------------------------------------------------------------------
# Bug 16: Best lap rounding — 3 decimal places
# ---------------------------------------------------------------------------

def test_total_time_three_decimals():
    """Total time seconds should display 3 decimal places."""
    from engine.race_dashboard import _format_time_hms

    result = _format_time_hms(90.1234)
    # Should show 3 decimal places for seconds portion
    assert "90.123" in result or "30.123" in result


def test_best_lap_three_decimals():
    """Best lap time should display 3 decimal places."""
    from engine.race_dashboard import _format_lap_time

    result = _format_lap_time(90.1234)
    assert ".123" in result


def test_total_and_best_same_precision():
    """total_time and best_lap should use same decimal precision."""
    from engine.race_dashboard import _format_lap_time, _format_time_hms

    # Both formatting functions should produce the same number of
    # decimal places for the seconds portion
    t1 = _format_time_hms(65.1234)   # 1:05.xxx
    t2 = _format_lap_time(65.1234)   # 1:05.xxx
    # Extract decimal part after last '.'
    dec1 = t1.split(".")[-1]
    dec2 = t2.split(".")[-1]
    assert len(dec1) == len(dec2) == 3
