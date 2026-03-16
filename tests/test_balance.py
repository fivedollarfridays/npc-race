"""Balance tests for NPC Race seed cars (T1.9).

Runs all 5 seed cars on representative tracks (power, technical, balanced)
and verifies competitive balance: no single car dominates all track types.
"""

import json
import os
import tempfile
from collections import Counter

from engine.race_runner import run_race


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CAR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cars")

# Representative tracks: 2 per character type
POWER_TRACKS = ["monza", "spa"]
TECHNICAL_TRACKS = ["monaco", "singapore"]
BALANCED_TRACKS = ["silverstone", "suzuka"]
ALL_TEST_TRACKS = POWER_TRACKS + TECHNICAL_TRACKS + BALANCED_TRACKS

ALL_CAR_NAMES = ["BrickHouse", "GlassCanon", "GooseLoose", "Silky", "SlipStream"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_race_get_results(track_name: str, laps: int = 2) -> list[dict]:
    """Run a race on the given track and return results."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out = f.name
    try:
        run_race(car_dir=CAR_DIR, track_name=track_name, laps=laps, output=out)
        with open(out) as f:
            replay = json.load(f)
        return replay["results"]
    finally:
        os.unlink(out)


def _get_winner(track_name: str, laps: int = 2) -> str:
    """Return the name of the P1 finisher on the given track."""
    results = _run_race_get_results(track_name, laps)
    for r in results:
        if r["position"] == 1:
            return r["name"]
    return ""


def _get_all_winners() -> dict[str, str]:
    """Return {track_name: winner_name} for all test tracks."""
    return {track: _get_winner(track) for track in ALL_TEST_TRACKS}


# ---------------------------------------------------------------------------
# Cycle 1: Races complete and results are deterministic
# ---------------------------------------------------------------------------

class TestRaceCompletion:
    """All 5 cars should finish on each representative track."""

    def test_all_cars_finish_on_all_tracks(self):
        for track in ALL_TEST_TRACKS:
            results = _run_race_get_results(track, laps=2)
            finished = [r for r in results if r["finished"]]
            assert len(finished) == 5, (
                f"Not all 5 cars finished on {track}: "
                f"{len(finished)} finished"
            )

    def test_results_are_deterministic(self):
        """Running the same race twice should produce identical results."""
        results_a = _run_race_get_results("monza", laps=2)
        results_b = _run_race_get_results("monza", laps=2)
        names_a = [r["name"] for r in results_a]
        names_b = [r["name"] for r in results_b]
        assert names_a == names_b

    def test_all_five_cars_present(self):
        results = _run_race_get_results("silverstone", laps=2)
        names = sorted(r["name"] for r in results)
        assert names == ALL_CAR_NAMES


# ---------------------------------------------------------------------------
# Cycle 2: No single car dominates
# ---------------------------------------------------------------------------

class TestNoDominance:
    """No single car should win more than 60% of tracks."""

    def test_no_car_wins_more_than_60_percent(self):
        winners = _get_all_winners()
        win_counts = Counter(winners.values())
        threshold = len(ALL_TEST_TRACKS) * 0.6
        for car, count in win_counts.items():
            assert count <= threshold, (
                f"{car} wins {count}/{len(ALL_TEST_TRACKS)} tracks "
                f"({count/len(ALL_TEST_TRACKS):.0%}), exceeds 60% threshold. "
                f"Wins: {winners}"
            )

    def test_at_least_two_different_winners(self):
        winners = _get_all_winners()
        unique = set(winners.values())
        assert len(unique) >= 2, (
            f"Only {len(unique)} unique winner(s) across all tracks: {winners}"
        )


# ---------------------------------------------------------------------------
# Cycle 3: Track character affects outcomes
# ---------------------------------------------------------------------------

class TestTrackCharacterDiversity:
    """Power and technical tracks should favor different cars."""

    def test_power_vs_technical_have_different_winners(self):
        """At least one power track winner differs from technical winners."""
        power_winners = {_get_winner(t) for t in POWER_TRACKS}
        tech_winners = {_get_winner(t) for t in TECHNICAL_TRACKS}
        # The union should have more than 1 car, meaning not all identical
        combined = power_winners | tech_winners
        assert len(combined) >= 2, (
            f"Power and technical tracks have identical winners: "
            f"power={power_winners}, technical={tech_winners}"
        )

    def test_no_single_car_wins_all_power_and_all_technical(self):
        """No car should sweep both power AND technical tracks."""
        power_winners = [_get_winner(t) for t in POWER_TRACKS]
        tech_winners = [_get_winner(t) for t in TECHNICAL_TRACKS]
        # If one car wins all power and all technical, balance is broken
        all_same = (
            len(set(power_winners)) == 1
            and len(set(tech_winners)) == 1
            and power_winners[0] == tech_winners[0]
        )
        assert not all_same, (
            f"One car sweeps both power and technical: "
            f"power={power_winners}, technical={tech_winners}"
        )
