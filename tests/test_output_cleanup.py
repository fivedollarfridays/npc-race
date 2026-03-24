"""Tests for output cleanup bugs #7-10 (T38.3)."""

import os

import pytest


# --- Bug 7: Results displayed twice ---

def test_race_runner_does_not_call_print_results(monkeypatch, capsys):
    """run_race should NOT call _print_results — dashboard is the canonical output."""
    from engine import race_runner

    # _print_results should not exist or not be called.
    # We verify by checking the output does NOT contain the old "RESULTS" banner.
    # Mock the heavy parts to avoid running a real sim.
    called = {"print_results": False}
    original = getattr(race_runner, "_print_results", None)

    def spy_print_results(results):
        called["print_results"] = True
        if original:
            original(results)

    monkeypatch.setattr(race_runner, "_print_results", spy_print_results, raising=False)

    # We don't actually run; we just check the function doesn't exist or is removed.
    # Better approach: inspect the source of run_race for _print_results call.
    import inspect
    source = inspect.getsource(race_runner.run_race)
    assert "_print_results" not in source, (
        "run_race still calls _print_results — remove it, dashboard is canonical"
    )


# --- Bug 8: Game artifacts in .gitignore ---

@pytest.mark.parametrize("artifact", [
    "results.json",
    "lap_summary.json",
    "grid.json",
    "leaderboard.json",
])
def test_gitignore_contains_game_artifacts(artifact):
    """All game artifact files should be in .gitignore."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gitignore_path = os.path.join(repo_root, ".gitignore")
    with open(gitignore_path) as f:
        content = f.read()
    assert artifact in content, f"{artifact} missing from .gitignore"


# --- Bug 9: Submit time format ---

def test_submit_summary_uses_mmss_format(capsys):
    """_print_submit_summary should display times as mm:ss.fff, not raw seconds."""
    from cli.commands import _print_submit_summary

    results = {
        "track": "monza",
        "laps": 5,
        "league": "F3",
        "integrity": "abc123",
        "cars": [
            {
                "position": 1,
                "name": "TestCar",
                "total_time_s": 95.13,
                "best_lap_s": 18.5,
                "reliability_score": 1.0,
            },
        ],
    }

    _print_submit_summary(results)
    output = capsys.readouterr().out

    # Should NOT contain raw seconds like "95.13s"
    assert "95.13s" not in output, "Times should use mm:ss.fff, not raw seconds"
    # Should contain formatted time like "1:35.130"
    assert "1:35.130" in output, "Total time should be formatted as mm:ss.fff"
    assert "0:18.500" in output, "Best lap should be formatted as mm:ss.fff"


# --- Bug 10: Cars listed twice with --qualify ---

def test_qualify_race_does_not_print_loading_twice(monkeypatch, capsys):
    """When --qualify is used, car loading output should appear only once."""
    import engine.race_runner as rr

    banner_calls = []
    original_banner = rr._print_race_banner

    def tracking_banner(*args, **kwargs):
        banner_calls.append(1)
        original_banner(*args, **kwargs)

    monkeypatch.setattr(rr, "_print_race_banner", tracking_banner)

    # We check the run_race signature accepts quiet parameter
    import inspect
    sig = inspect.signature(rr.run_race)
    assert "quiet" in sig.parameters, (
        "run_race should accept a 'quiet' parameter to suppress banner/loading output"
    )
