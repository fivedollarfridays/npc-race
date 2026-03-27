"""Unit tests for engine/league_gates.py — league detection and filtering."""

from engine.league_gates import _detect_league, _filter_car, apply_league_gates


def _make_car(name="TestCar", loaded_parts=None, source=""):
    """Build a minimal car dict for gate testing."""
    return {
        "name": name,
        "CAR_NAME": name,
        "_loaded_parts": loaded_parts or [],
        "_source": source,
    }


class TestDetectLeague:
    """Tests for _detect_league auto-detection."""

    def test_no_parts_detects_f3(self):
        cars = [_make_car()]
        league, label = _detect_league(cars, None)
        assert league == "F3"
        assert "auto-detected" in label

    def test_explicit_league_passes_through(self):
        cars = [_make_car()]
        league, label = _detect_league(cars, "F1")
        assert league == "F1"
        assert label == "F1"

    def test_f2_parts_detect_f2(self):
        cars = [_make_car(loaded_parts=["suspension"])]
        league, label = _detect_league(cars, None)
        assert league == "F2"

    def test_mixed_fleet_picks_highest(self):
        cars = [
            _make_car(name="A", loaded_parts=[]),
            _make_car(name="B", loaded_parts=["suspension"]),
        ]
        league, _ = _detect_league(cars, None)
        # B is F2, A is F3 -> max is F2
        assert league == "F2"


class TestFilterCar:
    """Tests for _filter_car validation logic."""

    def test_car_with_no_parts_passes_any_league(self):
        car = _make_car()
        result = _filter_car(car, "F3", "F3", verbose=False)
        assert result is True
        assert car["league"] == "F3"
        assert "reliability_score" in car

    def test_car_with_invalid_part_rejected_in_explicit_league(self):
        # brake_bias is NOT in F3 allowed parts
        car = _make_car(loaded_parts=["brake_bias"])
        result = _filter_car(car, "F3", "F3", verbose=False)
        assert result is False

    def test_car_passes_when_league_is_none(self):
        # When league=None, no part validation is applied
        car = _make_car(loaded_parts=["brake_bias"])
        result = _filter_car(car, None, "F3", verbose=False)
        assert result is True

    def test_verbose_prints_car_status(self, capsys):
        car = _make_car(name="AlphaBot")
        _filter_car(car, "F3", "F3", verbose=True)
        captured = capsys.readouterr()
        assert "AlphaBot" in captured.out


class TestApplyLeagueGates:
    """Tests for the top-level apply_league_gates function."""

    def test_returns_filtered_cars_and_league(self):
        cars = [_make_car(name="A"), _make_car(name="B")]
        filtered, league = apply_league_gates(cars, None)
        assert len(filtered) == 2
        assert league == "F3"

    def test_verbose_false_prints_summary(self, capsys):
        cars = [_make_car()]
        apply_league_gates(cars, None, verbose=False)
        captured = capsys.readouterr()
        assert "cars validated" in captured.out

    def test_verbose_true_prints_league_header(self, capsys):
        cars = [_make_car()]
        apply_league_gates(cars, None, verbose=True)
        captured = capsys.readouterr()
        assert "=== League:" in captured.out

    def test_rejects_invalid_parts_in_explicit_league(self):
        cars = [
            _make_car(name="Good"),
            _make_car(name="Bad", loaded_parts=["brake_bias"]),
        ]
        filtered, league = apply_league_gates(cars, "F3")
        names = [c["name"] for c in filtered]
        assert "Good" in names
        assert "Bad" not in names
