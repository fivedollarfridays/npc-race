"""Tests for quiet/verbose league output in race_runner."""


# ---------------------------------------------------------------------------
# Cycle 1: _apply_league_gates respects verbose flag
# ---------------------------------------------------------------------------

def _make_car(name: str = "TestCar", parts: list[str] | None = None) -> dict:
    """Build a minimal car dict for league gate tests."""
    return {
        "name": name,
        "CAR_NAME": name,
        "_loaded_parts": parts or [],
        "engine_power": 500,
        "downforce": 1.0,
        "drag": 0.3,
        "tire_deg_rate": 0.01,
        "brake_balance": 0.55,
        "front_wing_angle": 12.0,
        "cooling": 0.5,
    }


class TestQuietMode:
    """When verbose=False, league output should be minimal."""

    def test_quiet_mode_no_advisory(self, capsys):
        """Per-car advisory lines should be suppressed in quiet mode."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [_make_car("Alpha"), _make_car("Bravo")]
        _apply_league_gates(cars, league=None, verbose=False)

        out = capsys.readouterr().out
        assert "Advisory" not in out

    def test_quiet_mode_no_custom_parts_line(self, capsys):
        """Per-car 'custom parts' lines should be suppressed in quiet mode."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [_make_car("Alpha"), _make_car("Bravo")]
        _apply_league_gates(cars, league=None, verbose=False)

        out = capsys.readouterr().out
        assert "custom parts" not in out

    def test_quiet_mode_no_quality_line(self, capsys):
        """Per-car Quality lines should be suppressed in quiet mode."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [_make_car("Alpha"), _make_car("Bravo")]
        _apply_league_gates(cars, league=None, verbose=False)

        out = capsys.readouterr().out
        assert "Quality" not in out

    def test_quiet_mode_summary_line(self, capsys):
        """Quiet mode should still print a summary with car count."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [_make_car("Alpha"), _make_car("Bravo")]
        _apply_league_gates(cars, league=None, verbose=False)

        out = capsys.readouterr().out
        assert "cars validated" in out
        assert "2" in out


class TestVerboseMode:
    """When verbose=True, league output should include all details."""

    def test_verbose_mode_has_advisory_or_quality(self, capsys):
        """Verbose mode should print per-car detail lines."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [_make_car("Alpha"), _make_car("Bravo")]
        _apply_league_gates(cars, league=None, verbose=True)

        out = capsys.readouterr().out
        # Verbose should have per-car details (Advisory or Quality lines)
        assert "Advisory" in out or "Quality" in out or "custom parts" in out

    def test_verbose_mode_has_car_names(self, capsys):
        """Verbose mode should print individual car names."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [_make_car("Alpha"), _make_car("Bravo")]
        _apply_league_gates(cars, league=None, verbose=True)

        out = capsys.readouterr().out
        assert "Alpha" in out
        assert "Bravo" in out


class TestDefaultVerbose:
    """Default verbose behavior (backward compatibility)."""

    def test_default_verbose_is_false(self):
        """run_race signature should default verbose to False."""
        import inspect
        from engine.race_runner import run_race

        sig = inspect.signature(run_race)
        assert sig.parameters["verbose"].default is False


class TestCliVerboseFlag:
    """CLI parsers should accept --verbose / -v."""

    def test_run_parser_verbose_flag(self):
        """'run' subparser should accept --verbose."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["run", "--verbose"])
        assert args.verbose is True

    def test_run_parser_verbose_short_flag(self):
        """'run' subparser should accept -v."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["run", "-v"])
        assert args.verbose is True

    def test_run_parser_no_verbose_default(self):
        """'run' subparser should default verbose to False."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["run"])
        assert args.verbose is False

    def test_race_parser_verbose_flag(self):
        """'race' subparser should accept --verbose."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["race", "--verbose"])
        assert args.verbose is True
