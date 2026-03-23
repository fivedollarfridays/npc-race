"""End-to-end tests for the submission pipeline: run -> results -> submit."""

import json
import os
import tempfile

from engine.race_runner import run_race
from engine.results import verify_integrity


class TestRunProducesResults:
    """Cycle 1: run_race() produces results alongside replay."""

    def test_run_produces_results_file(self):
        """run_race() produces both replay.json and results.json."""
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            run_race(car_dir="cars", track_name="monza", laps=1, output=output)
            results_path = os.path.join(td, "results.json")
            assert os.path.isfile(results_path), "results.json not created"

    def test_results_has_all_fields(self):
        """Results file has version, track, laps, league, timestamp, cars, integrity."""
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            run_race(car_dir="cars", track_name="monza", laps=1, output=output)
            results_path = os.path.join(td, "results.json")
            with open(results_path) as f:
                data = json.load(f)
            required = ["version", "track", "laps", "league", "timestamp", "cars", "integrity"]
            for field in required:
                assert field in data, f"Missing field: {field}"

    def test_results_file_small(self):
        """Results file is much smaller than replay file."""
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            run_race(car_dir="cars", track_name="monza", laps=1, output=output)
            results_path = os.path.join(td, "results.json")
            results_size = os.path.getsize(results_path)
            assert results_size < 50_000, f"results.json too large: {results_size} bytes"


class TestIntegrityVerification:
    """Cycle 2: integrity hash validation on pipeline output."""

    def test_integrity_valid(self):
        """Results file passes integrity verification."""
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            run_race(car_dir="cars", track_name="monza", laps=1, output=output)
            results_path = os.path.join(td, "results.json")
            with open(results_path) as f:
                data = json.load(f)
            assert verify_integrity(data), "Integrity check failed on fresh results"

    def test_tamper_breaks_integrity(self):
        """Modifying a result field breaks the integrity hash."""
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            run_race(car_dir="cars", track_name="monza", laps=1, output=output)
            results_path = os.path.join(td, "results.json")
            with open(results_path) as f:
                data = json.load(f)
            # Tamper with first car's lap time
            data["cars"][0]["total_time_s"] = 0.001
            assert not verify_integrity(data), "Tampered results should fail integrity"


class TestSubmitCommand:
    """Cycle 3: cmd_submit validates pipeline results end-to-end."""

    def test_submit_validates_pipeline_results(self):
        """cmd_submit() successfully validates results from run_race()."""
        from cli.commands import cmd_submit

        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            run_race(car_dir="cars", track_name="monza", laps=1, output=output)
            results_path = os.path.join(td, "results.json")

            class Args:
                results_file = results_path

            ret = cmd_submit(Args())
            assert ret == 0, "cmd_submit should return 0 for valid results"

    def test_submit_rejects_tampered(self):
        """cmd_submit() rejects tampered results."""
        from cli.commands import cmd_submit

        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            run_race(car_dir="cars", track_name="monza", laps=1, output=output)
            results_path = os.path.join(td, "results.json")

            with open(results_path) as f:
                data = json.load(f)
            data["cars"][0]["total_time_s"] = 999.999
            with open(results_path, "w") as f:
                json.dump(data, f)

            class Args:
                results_file = results_path

            ret = cmd_submit(Args())
            assert ret == 1, "cmd_submit should return 1 for tampered results"


class TestTournamentResults:
    """Cycle 4: tournament produces per-race results files."""

    def test_tournament_produces_per_race_results(self):
        """Each race in a tournament produces its own results file."""
        from cli.commands import cmd_tournament

        with tempfile.TemporaryDirectory() as td:
            output_dir = os.path.join(td, "output")

            class Args:
                tracks = "monza"
                races = 2
                laps = 1
                car_dir = "cars"
                data_dir = os.path.join(td, "data")
                output_dir_val = output_dir

            args = Args()
            args.output_dir = output_dir

            cmd_tournament(args)

            # Each race should produce a replay and a results file
            for i in [1, 2]:
                replay = os.path.join(output_dir, f"race_{i}_monza.json")
                results = os.path.join(output_dir, f"race_{i}_monza_results.json")
                assert os.path.isfile(replay), f"Missing replay for race {i}"
                assert os.path.isfile(results), f"Missing results for race {i}"

                with open(results) as f:
                    data = json.load(f)
                assert verify_integrity(data), f"Race {i} results failed integrity"


class TestExistingBehavior:
    """Cycle 4: existing run_race() behavior unchanged."""

    def test_existing_race_tests_unaffected(self):
        """run_race() still returns a list of result dicts."""
        with tempfile.TemporaryDirectory() as td:
            output = os.path.join(td, "replay.json")
            results = run_race(
                car_dir="cars", track_name="monza", laps=1, output=output,
            )
            assert isinstance(results, list)
            assert len(results) >= 5
            # Each result has position and name
            for r in results:
                assert "position" in r
                assert "name" in r
                assert "finished" in r
