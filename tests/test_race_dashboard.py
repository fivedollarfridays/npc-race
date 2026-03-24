"""Tests for engine.race_dashboard — race summary dashboard."""

from __future__ import annotations


def _make_results(n: int = 3, laps: int = 5) -> list[dict]:
    """Build a minimal results list with n cars."""
    names = ["GlassCanon", "NightFury", "Tortoise", "Rocket", "Snail"][:n]
    base_time = 300.0  # 5 min
    results = []
    for i, name in enumerate(names):
        total = base_time + i * 5.0
        best = 58.0 + i * 0.5
        results.append({
            "name": name,
            "position": i + 1,
            "total_time_s": total,
            "best_lap_s": best,
            "finished": True,
            "pit_stops": 2 - (i % 2),
            "lap_times": [best + j * 0.1 for j in range(laps)],
            "color": "#ff0000",
            "finish_tick": int(total * 30),
        })
    return results


def _make_lap_summaries(results: list[dict], laps: int = 5) -> dict[str, list[dict]]:
    """Build minimal lap summaries keyed by car name."""
    summaries: dict[str, list[dict]] = {}
    for r in results:
        car_laps = []
        for lap_num in range(1, laps + 1):
            car_laps.append({
                "lap": lap_num,
                "time_s": r["best_lap_s"] + (lap_num - 1) * 0.1,
                "position": r["position"],
                "tire_compound": "medium" if lap_num <= 3 else "hard",
                "tire_wear": lap_num * 0.1,
                "pit_stop": lap_num == 3,
                "fuel_remaining_pct": 1.0 - lap_num * 0.15,
            })
        summaries[r["name"]] = car_laps
    return summaries


# --- Cycle 1: Standings ---

def test_standings_contains_all_cars():
    """All car names must appear in the standings section."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(5)
    dashboard = generate_dashboard(results, track_name="monza", laps=5)
    for r in results:
        assert r["name"] in dashboard


def test_standings_shows_gap_to_leader():
    """Non-leader cars should show a gap like '+5.0'."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(3)
    dashboard = generate_dashboard(results, track_name="monza", laps=5)
    # P2 is 5s behind leader
    assert "+5.0" in dashboard


def test_standings_shows_race_header():
    """Dashboard should show track name and lap count in header."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(2)
    dashboard = generate_dashboard(results, track_name="monza", laps=53)
    assert "MONZA" in dashboard.upper()
    assert "53" in dashboard


# --- Cycle 2: Lap chart ---

def test_lap_chart_shows_positions():
    """Lap chart should show position numbers for each car."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(3, laps=10)
    lap_sums = _make_lap_summaries(results, laps=10)
    dashboard = generate_dashboard(results, lap_sums, track_name="monza", laps=10)
    assert "LAP CHART" in dashboard
    # Should show car names in the chart
    assert "GlassCanon" in dashboard
    assert "NightFury" in dashboard


def test_lap_chart_skipped_without_summaries():
    """Lap chart should not appear when lap_summaries is None (live mode)."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(3)
    dashboard = generate_dashboard(results, lap_summaries=None, track_name="monza", laps=5)
    assert "LAP CHART" not in dashboard


# --- Cycle 3: Pit stops ---

def test_pit_stops_listed():
    """Pit stop section should show compound transitions per car."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(2, laps=5)
    lap_sums = _make_lap_summaries(results, laps=5)
    dashboard = generate_dashboard(results, lap_sums, track_name="monza", laps=5)
    assert "PIT STOPS" in dashboard
    # Each car pits on L3 (medium->hard transition in our test data)
    assert "L3" in dashboard
    assert "medium" in dashboard


def test_pit_stops_skipped_without_summaries():
    """Pit stop section hidden in live mode (no lap_summaries)."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(2)
    dashboard = generate_dashboard(results, lap_summaries=None, track_name="monza", laps=5)
    assert "PIT STOPS" not in dashboard


# --- Cycle 4: Key moments + width constraint ---

def test_key_moments_fastest_lap():
    """Key moments should highlight the fastest lap."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(3, laps=5)
    dashboard = generate_dashboard(results, track_name="monza", laps=5)
    assert "KEY MOMENTS" in dashboard
    assert "FASTEST LAP" in dashboard
    # GlassCanon has best lap of 58.0s
    assert "GlassCanon" in dashboard


def test_dashboard_fits_120_columns():
    """No line in the dashboard should exceed 120 characters."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(5, laps=50)
    lap_sums = _make_lap_summaries(results, laps=50)
    dashboard = generate_dashboard(results, lap_sums, track_name="monza", laps=50)
    for i, line in enumerate(dashboard.split("\n"), 1):
        assert len(line) <= 120, f"Line {i} is {len(line)} chars: {line!r}"


def test_dashboard_handles_no_lap_summaries():
    """Live mode: only standings + key moments, no lap chart or pit data."""
    from engine.race_dashboard import generate_dashboard

    results = _make_results(3)
    dashboard = generate_dashboard(results, lap_summaries=None, track_name="monza", laps=5)
    assert "RACE RESULTS" in dashboard
    assert "KEY MOMENTS" in dashboard
    assert "LAP CHART" not in dashboard
    assert "PIT STOPS" not in dashboard


# --- Cycle 5: Integration wiring ---

def test_integration_dashboard_called_in_race_runner():
    """race_runner.run_race must call generate_dashboard (import present)."""
    import inspect
    from engine import race_runner

    source = inspect.getsource(race_runner)
    assert "generate_dashboard" in source, (
        "generate_dashboard not found in race_runner source"
    )
