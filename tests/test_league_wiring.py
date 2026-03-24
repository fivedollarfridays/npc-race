"""Tests for league system wiring into race runner and CLI."""

from engine.league_system import LEAGUE_PARTS
from engine.parts_api import CAR_PARTS


# --- Sample source snippets for quality gate tests ---

CLEAN_SOURCE = '''\
def shift_gear(speed: float, rpm: int) -> int:
    if rpm > 7000:
        return min(8, speed // 40 + 1)
    return max(1, int(speed // 50))
'''

MESSY_SOURCE = '''\
def shift_gear(speed, rpm):
    if speed > 300:
        if rpm > 8000:
            if speed > 350:
                if rpm > 9000:
                    if speed > 380:
                        if rpm > 9500:
                            if speed > 390:
                                if rpm > 9800:
                                    if speed > 395:
                                        if rpm > 9900:
                                            if speed > 398:
                                                if rpm > 9950:
                                                    if speed > 399:
                                                        if rpm > 9980:
                                                            if speed > 399.5:
                                                                if rpm > 9990:
                                                                    return 8
                                                                return 7
                                                            return 7
                                                        return 6
                                                    return 6
                                                return 5
                                            return 5
                                        return 4
                                    return 4
                                return 3
                            return 3
                        return 2
                    return 2
                return 1
            return 1
        return 1
    return 1
'''


def _make_car(name, loaded_parts=None, source="", project_dir=None):
    """Create a minimal car dict for testing."""
    car = {
        "name": name,
        "_loaded_parts": loaded_parts or [],
    }
    if source:
        car["_source"] = source
    if project_dir:
        car["_project_dir"] = project_dir
    return car


class TestRunRaceLeagueParam:
    """run_race() accepts league kwarg without breaking existing calls."""

    def test_run_race_accepts_league_param(self):
        """run_race should accept league kwarg without error."""
        import inspect
        from engine.race_runner import run_race

        sig = inspect.signature(run_race)
        assert "league" in sig.parameters
        assert sig.parameters["league"].default is None


class TestApplyLeagueGates:
    """_apply_league_gates() handles detection, validation, and filtering."""

    def test_auto_detect_league_f3(self):
        """Without league, cars with few parts get F3."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("CarA", ["gearbox"]),
            _make_car("CarB", ["gearbox", "cooling"]),
        ]
        filtered, effective_league = _apply_league_gates(cars, league=None)
        assert effective_league == "F3"
        assert len(filtered) == 2
        assert filtered[0]["league"] == "F3"

    def test_auto_detect_uses_highest_tier(self):
        """Auto-detect picks the highest league among all cars."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("F3Car", ["gearbox"]),
            _make_car("F2Car", list(LEAGUE_PARTS["F2"])),
        ]
        filtered, effective_league = _apply_league_gates(cars, league=None)
        assert effective_league == "F2"

    def test_specified_league_validates(self):
        """When league is specified, cars are validated against it."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("ValidCar", ["gearbox", "cooling"]),
            _make_car("InvalidCar", ["gearbox", "engine_map"]),
        ]
        # F3 does not allow engine_map
        filtered, effective_league = _apply_league_gates(cars, league="F3")
        assert effective_league == "F3"
        # InvalidCar has engine_map which is not in F3
        names = [c["name"] for c in filtered]
        assert "ValidCar" in names
        assert "InvalidCar" not in names

    def test_enforced_gate_skips_bad_car(self):
        """Car failing F1 quality gate is skipped."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("GoodCar", list(CAR_PARTS), source=CLEAN_SOURCE),
            _make_car("BadCar", list(CAR_PARTS), source=MESSY_SOURCE),
        ]
        filtered, effective_league = _apply_league_gates(cars, league="F1")
        assert effective_league == "F1"
        names = [c["name"] for c in filtered]
        assert "GoodCar" in names
        assert "BadCar" not in names

    def test_advisory_league_keeps_all_cars(self):
        """F3 advisory gates don't reject cars."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("Car1", ["gearbox"], source=MESSY_SOURCE),
            _make_car("Car2", ["gearbox"], source=CLEAN_SOURCE),
        ]
        filtered, effective_league = _apply_league_gates(cars, league="F3")
        assert len(filtered) == 2

    def test_car_gets_league_field(self):
        """Each car dict gets a 'league' key after processing."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("CarA", ["gearbox"]),
            _make_car("CarB", ["gearbox"]),
        ]
        filtered, _ = _apply_league_gates(cars, league="F3")
        for car in filtered:
            assert car["league"] == "F3"


class TestLeagueConsoleOutput:
    """League wiring prints quality report info."""

    def test_prints_league_header(self, capsys):
        """Output includes league header line."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("CarA", ["gearbox"]),
            _make_car("CarB", ["cooling"]),
        ]
        _apply_league_gates(cars, league="F3")
        out = capsys.readouterr().out
        assert "League: F3" in out

    def test_auto_detect_shows_auto_detected(self, capsys):
        """Auto-detected league says so in output."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("CarA", ["gearbox"]),
            _make_car("CarB", ["cooling"]),
        ]
        _apply_league_gates(cars, league=None)
        out = capsys.readouterr().out
        assert "auto-detected" in out.lower()

    def test_rejected_car_prints_reason(self, capsys):
        """Rejected car shows REJECTED with reason."""
        from engine.league_gates import apply_league_gates as _apply_league_gates

        cars = [
            _make_car("GoodCar", list(CAR_PARTS), source=CLEAN_SOURCE),
            _make_car("BadCar", list(CAR_PARTS), source=MESSY_SOURCE),
        ]
        _apply_league_gates(cars, league="F1", verbose=True)
        out = capsys.readouterr().out
        assert "REJECTED" in out
        assert "BadCar" in out


class TestCliLeagueFlag:
    """CLI --league argument is parsed and forwarded."""

    def test_cli_parser_has_league_flag(self):
        """The 'run' subparser accepts --league."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["run", "--league", "F1"])
        assert args.league == "F1"

    def test_cli_league_default_none(self):
        """--league defaults to None when not specified."""
        from cli.main import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["run"])
        assert args.league is None

    def test_cli_league_choices(self):
        """--league only accepts valid tier names."""
        from cli.main import _build_parser

        parser = _build_parser()
        try:
            parser.parse_args(["run", "--league", "INVALID"])
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass  # argparse exits on invalid choice
