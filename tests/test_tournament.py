"""Tests for tournament mode CLI command."""

import json
import os



# ── Cycle 1: F1_POINTS constant ──


class TestF1Points:
    """Test that F1 championship points are correctly defined."""

    def test_f1_points_exists(self):
        """F1_POINTS list should be importable from cli.commands."""
        from cli.commands import F1_POINTS

        assert isinstance(F1_POINTS, list)

    def test_f1_points_values(self):
        """F1_POINTS should match official F1 top-10 scoring."""
        from cli.commands import F1_POINTS

        expected = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
        assert F1_POINTS == expected

    def test_f1_points_no_points_outside_top10(self):
        """Only 10 scoring positions."""
        from cli.commands import F1_POINTS

        assert len(F1_POINTS) == 10


# ── Cycle 2: Tournament subparser and dispatch ──


class TestTournamentSubparser:
    """Test that tournament subcommand is wired into CLI."""

    def test_tournament_subcommand_exists(self):
        """tournament should be recognized as a valid subcommand."""
        from cli.main import _build_parser

        parser = _build_parser()
        # Should not raise
        args = parser.parse_args(["tournament", "--tracks", "monaco"])
        assert args.command == "tournament"

    def test_tournament_dispatch_wired(self):
        """_DISPATCH should contain tournament -> cmd_tournament."""
        from cli.main import _DISPATCH

        assert "tournament" in _DISPATCH

    def test_cmd_tournament_callable(self):
        """cmd_tournament should be importable and callable."""
        from cli.commands import cmd_tournament

        assert callable(cmd_tournament)

    def test_tournament_default_args(self):
        """Tournament subparser should have correct defaults."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["tournament", "--tracks", "monaco"])
        assert args.races == 1
        assert args.laps == 5
        assert args.car_dir == "cars"
        assert args.data_dir is None
        assert args.output_dir == "tournaments"


# ── Cycle 3: Single-track tournament execution ──


def _make_fake_run_race(results_by_call):
    """Create a fake run_race that writes replay files with given results.

    Parameters
    ----------
    results_by_call : list[list[dict]]
        Each entry is the results list for one call to run_race.
        Each result dict needs at minimum "name" and "position".
    """
    call_idx = [0]
    calls = []

    def fake_run_race(**kwargs):
        idx = call_idx[0]
        call_idx[0] += 1
        calls.append(kwargs)
        results = results_by_call[idx]
        # Write a replay file like the real engine does
        replay = {"results": results, "frames": []}
        with open(kwargs["output"], "w") as f:
            json.dump(replay, f)
        return results

    return fake_run_race, calls


class TestTournamentExecution:
    """Test cmd_tournament runs races and produces output."""

    def test_single_track_single_race_produces_file(self, monkeypatch, tmp_path):
        """Tournament with 1 track, 1 race should produce 1 output file."""
        from cli import commands
        from cli.main import _build_parser

        results = [[
            {"name": "CarA", "position": 1, "finish_tick": 100, "finished": True},
            {"name": "CarB", "position": 2, "finish_tick": 110, "finished": True},
        ]]
        fake, calls = _make_fake_run_race(results)
        monkeypatch.setattr(commands, "run_race", fake)

        output_dir = str(tmp_path / "out")
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco",
            "--car-dir", str(tmp_path),
            "--output-dir", output_dir,
        ])
        commands.cmd_tournament(args)

        assert os.path.isfile(os.path.join(output_dir, "race_1_monaco.json"))

    def test_single_track_race_called_with_correct_args(self, monkeypatch, tmp_path):
        """run_race should be called with correct track, laps, data_dir."""
        from cli import commands
        from cli.main import _build_parser

        results = [[
            {"name": "CarA", "position": 1, "finish_tick": 100, "finished": True},
            {"name": "CarB", "position": 2, "finish_tick": 110, "finished": True},
        ]]
        fake, calls = _make_fake_run_race(results)
        monkeypatch.setattr(commands, "run_race", fake)

        output_dir = str(tmp_path / "out")
        car_dir = str(tmp_path / "cars")
        os.makedirs(car_dir)
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco", "--laps", "3",
            "--car-dir", car_dir,
            "--output-dir", output_dir,
        ])
        commands.cmd_tournament(args)

        assert len(calls) == 1
        assert calls[0]["track_name"] == "monaco"
        assert calls[0]["laps"] == 3
        assert calls[0]["car_dir"] == car_dir
        assert calls[0]["race_number"] == 1
        assert calls[0]["car_data_dir"] == os.path.join(car_dir, "data")


# ── Cycle 4: Multi-track, standings, race_number ──


class TestTournamentMultiTrack:
    """Test multi-track tournaments with standings accumulation."""

    def test_two_tracks_produces_two_files(self, monkeypatch, tmp_path):
        """Tournament with 2 tracks should produce 2 output files."""
        from cli import commands
        from cli.main import _build_parser

        race1 = [
            {"name": "CarA", "position": 1, "finish_tick": 100, "finished": True},
            {"name": "CarB", "position": 2, "finish_tick": 110, "finished": True},
        ]
        race2 = [
            {"name": "CarB", "position": 1, "finish_tick": 95, "finished": True},
            {"name": "CarA", "position": 2, "finish_tick": 105, "finished": True},
        ]
        fake, calls = _make_fake_run_race([race1, race2])
        monkeypatch.setattr(commands, "run_race", fake)

        output_dir = str(tmp_path / "out")
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco,monza",
            "--car-dir", str(tmp_path),
            "--output-dir", output_dir,
        ])
        commands.cmd_tournament(args)

        assert os.path.isfile(os.path.join(output_dir, "race_1_monaco.json"))
        assert os.path.isfile(os.path.join(output_dir, "race_2_monza.json"))

    def test_race_number_increments_across_tracks(self, monkeypatch, tmp_path):
        """race_number should increment: 1 for first race, 2 for second."""
        from cli import commands
        from cli.main import _build_parser

        race_results = [
            [{"name": "A", "position": 1, "finish_tick": 1, "finished": True}],
            [{"name": "A", "position": 1, "finish_tick": 1, "finished": True}],
        ]
        fake, calls = _make_fake_run_race(race_results)
        monkeypatch.setattr(commands, "run_race", fake)

        output_dir = str(tmp_path / "out")
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco,monza",
            "--car-dir", str(tmp_path),
            "--output-dir", output_dir,
        ])
        commands.cmd_tournament(args)

        assert calls[0]["race_number"] == 1
        assert calls[1]["race_number"] == 2

    def test_standings_accumulate_correctly(self, monkeypatch, tmp_path, capsys):
        """Points should accumulate: P1 in race1 + P2 in race2 = 25+18 = 43."""
        from cli import commands
        from cli.main import _build_parser

        race1 = [
            {"name": "CarA", "position": 1, "finish_tick": 100, "finished": True},
            {"name": "CarB", "position": 2, "finish_tick": 110, "finished": True},
        ]
        race2 = [
            {"name": "CarB", "position": 1, "finish_tick": 95, "finished": True},
            {"name": "CarA", "position": 2, "finish_tick": 105, "finished": True},
        ]
        fake, calls = _make_fake_run_race([race1, race2])
        monkeypatch.setattr(commands, "run_race", fake)

        output_dir = str(tmp_path / "out")
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco,monza",
            "--car-dir", str(tmp_path),
            "--output-dir", output_dir,
        ])
        commands.cmd_tournament(args)

        captured = capsys.readouterr()
        # Both should have 25+18 = 43 pts in final standings
        assert "43 pts" in captured.out

    def test_races_per_track(self, monkeypatch, tmp_path):
        """--races 2 on 1 track should produce 2 race files."""
        from cli import commands
        from cli.main import _build_parser

        race_results = [
            [{"name": "A", "position": 1, "finish_tick": 1, "finished": True}],
            [{"name": "A", "position": 1, "finish_tick": 1, "finished": True}],
        ]
        fake, calls = _make_fake_run_race(race_results)
        monkeypatch.setattr(commands, "run_race", fake)

        output_dir = str(tmp_path / "out")
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco", "--races", "2",
            "--car-dir", str(tmp_path),
            "--output-dir", output_dir,
        ])
        commands.cmd_tournament(args)

        assert len(calls) == 2
        assert calls[0]["race_number"] == 1
        assert calls[1]["race_number"] == 2
        assert os.path.isfile(os.path.join(output_dir, "race_1_monaco.json"))
        assert os.path.isfile(os.path.join(output_dir, "race_2_monaco.json"))


# ── Cycle 5: Output dir, data_dir, header ──


class TestTournamentEdgeCases:
    """Test output dir creation, data_dir default, and header printing."""

    def test_output_dir_created_if_missing(self, monkeypatch, tmp_path):
        """Output directory should be created automatically."""
        from cli import commands
        from cli.main import _build_parser

        results = [[
            {"name": "A", "position": 1, "finish_tick": 1, "finished": True},
        ]]
        fake, _ = _make_fake_run_race(results)
        monkeypatch.setattr(commands, "run_race", fake)

        output_dir = str(tmp_path / "deep" / "nested" / "out")
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco",
            "--car-dir", str(tmp_path),
            "--output-dir", output_dir,
        ])
        commands.cmd_tournament(args)

        assert os.path.isdir(output_dir)

    def test_custom_data_dir(self, monkeypatch, tmp_path):
        """--data-dir should override the default car_dir/data path."""
        from cli import commands
        from cli.main import _build_parser

        results = [[
            {"name": "A", "position": 1, "finish_tick": 1, "finished": True},
        ]]
        fake, calls = _make_fake_run_race(results)
        monkeypatch.setattr(commands, "run_race", fake)

        custom_data = str(tmp_path / "my_data")
        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco",
            "--car-dir", str(tmp_path),
            "--data-dir", custom_data,
            "--output-dir", str(tmp_path / "out"),
        ])
        commands.cmd_tournament(args)

        assert calls[0]["car_data_dir"] == custom_data

    def test_header_printed(self, monkeypatch, tmp_path, capsys):
        """Tournament should print header with tracks and config."""
        from cli import commands
        from cli.main import _build_parser

        results = [[
            {"name": "A", "position": 1, "finish_tick": 1, "finished": True},
        ]]
        fake, _ = _make_fake_run_race(results)
        monkeypatch.setattr(commands, "run_race", fake)

        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", "monaco",
            "--car-dir", str(tmp_path),
            "--output-dir", str(tmp_path / "out"),
        ])
        commands.cmd_tournament(args)

        captured = capsys.readouterr()
        assert "CHAMPIONSHIP TOURNAMENT" in captured.out
        assert "monaco" in captured.out
        assert "FINAL CHAMPIONSHIP STANDINGS" in captured.out

    def test_track_names_stripped_and_lowered(self, monkeypatch, tmp_path):
        """Track names with spaces/caps should be normalized."""
        from cli import commands
        from cli.main import _build_parser

        results = [[
            {"name": "A", "position": 1, "finish_tick": 1, "finished": True},
        ]]
        fake, calls = _make_fake_run_race(results)
        monkeypatch.setattr(commands, "run_race", fake)

        parser = _build_parser()
        args = parser.parse_args([
            "tournament", "--tracks", " Monaco ",
            "--car-dir", str(tmp_path),
            "--output-dir", str(tmp_path / "out"),
        ])
        commands.cmd_tournament(args)

        assert calls[0]["track_name"] == "monaco"
