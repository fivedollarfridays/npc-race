"""Tests for engine.league_system — league definitions and validation."""

from engine.league_system import (
    LEAGUE_PARTS,
    LEAGUE_TIERS,
    determine_league,
    generate_quality_report,
    validate_car_for_league,
)
from engine.parts_api import CAR_PARTS


# --- Sample source code for quality gate tests ---

CLEAN_SOURCE = '''\
def shift_gear(speed: float, rpm: int) -> int:
    """Select gear based on speed and RPM."""
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


def test_league_tiers_constant():
    """LEAGUE_TIERS has 4 entries in the correct order."""
    assert LEAGUE_TIERS == ["F3", "F2", "F1", "Championship"]


def test_determine_league_empty_parts():
    """No loaded parts -> F3."""
    car = {"_loaded_parts": []}
    assert determine_league(car) == "F3"


def test_determine_league_no_key():
    """Missing _loaded_parts key -> F3."""
    car = {}
    assert determine_league(car) == "F3"


def test_determine_league_f3_parts():
    """Only gearbox + strategy -> F3."""
    car = {"_loaded_parts": ["gearbox", "strategy"]}
    assert determine_league(car) == "F3"


def test_determine_league_f2_parts():
    """All 6 F2 parts -> F2."""
    car = {"_loaded_parts": list(LEAGUE_PARTS["F2"])}
    assert determine_league(car) == "F2"


def test_determine_league_f1_parts():
    """All 10 parts without project dir -> F1."""
    car = {"_loaded_parts": list(CAR_PARTS)}
    assert determine_league(car) == "F1"


def test_determine_league_championship():
    """All 10 parts + _project_dir -> Championship."""
    car = {"_loaded_parts": list(CAR_PARTS), "_project_dir": "/some/path"}
    assert determine_league(car) == "Championship"


def test_validate_f3_valid():
    """F3 car with gearbox + cooling passes validation."""
    car = {"_loaded_parts": ["gearbox", "cooling"]}
    result = validate_car_for_league(car, "F3")
    assert result.passed is True
    assert result.league == "F3"
    assert result.violations == []


def test_validate_f3_invalid():
    """F3 car with engine_map -> violation."""
    car = {"_loaded_parts": ["gearbox", "engine_map"]}
    result = validate_car_for_league(car, "F3")
    assert result.passed is False
    assert len(result.violations) == 1
    assert "engine_map" in result.violations[0]
    assert "F3" in result.violations[0]


def test_validate_f1_allows_all():
    """F1 allows all 10 parts."""
    car = {"_loaded_parts": list(CAR_PARTS)}
    result = validate_car_for_league(car, "F1")
    assert result.passed is True
    assert result.violations == []


def test_league_result_has_violations():
    """Rejected car has specific violation messages."""
    car = {"_loaded_parts": ["engine_map", "brake_bias", "gearbox"]}
    result = validate_car_for_league(car, "F3")
    assert result.passed is False
    assert len(result.violations) == 2
    violation_text = " ".join(result.violations)
    assert "engine_map" in violation_text
    assert "brake_bias" in violation_text


# ── Quality Gate Tests ──────────────────────────────────────────────


class TestQualityGates:
    """Tests for generate_quality_report() quality gates."""

    def test_f3_advisory_always_passes(self):
        """F3 quality report always passes, even with bad code."""
        car = {"_source": MESSY_SOURCE, "_loaded_parts": ["gearbox"]}
        report = generate_quality_report(car, "F3")
        assert report.passed is True
        assert report.league == "F3"
        assert report.blocking_violations == []

    def test_f3_advisory_has_messages(self):
        """F3 report includes informational messages about code quality."""
        car = {"_source": MESSY_SOURCE, "_loaded_parts": ["gearbox"]}
        report = generate_quality_report(car, "F3")
        assert len(report.advisory_messages) > 0
        # Messages should mention what would happen at higher tiers
        combined = " ".join(report.advisory_messages)
        assert "F1" in combined or "Championship" in combined

    def test_f2_advisory_always_passes(self):
        """F2 quality report always passes, even with bad code."""
        car = {"_source": MESSY_SOURCE, "_loaded_parts": list(LEAGUE_PARTS["F2"])}
        report = generate_quality_report(car, "F2")
        assert report.passed is True
        assert report.blocking_violations == []

    def test_f1_enforced_clean_code_passes(self):
        """F1 with clean code passes the enforced gate."""
        car = {"_source": CLEAN_SOURCE, "_loaded_parts": list(CAR_PARTS)}
        report = generate_quality_report(car, "F1")
        assert report.passed is True
        assert report.blocking_violations == []
        assert report.reliability_score >= 0.88

    def test_f1_enforced_high_cc_fails(self):
        """F1 with high CC is rejected."""
        car = {"_source": MESSY_SOURCE, "_loaded_parts": list(CAR_PARTS)}
        report = generate_quality_report(car, "F1")
        assert report.passed is False
        assert len(report.blocking_violations) > 0
        combined = " ".join(report.blocking_violations)
        assert "complexity" in combined.lower() or "lint" in combined.lower()

    def test_championship_requires_reliability(self):
        """Championship needs reliability >= 0.88."""
        car = {"_source": CLEAN_SOURCE, "_loaded_parts": list(CAR_PARTS),
               "_project_dir": "/p"}
        report = generate_quality_report(car, "Championship")
        assert report.passed is True
        assert report.reliability_score >= 0.88

    def test_championship_low_reliability_fails(self):
        """Championship with messy code is rejected with specific feedback."""
        car = {"_source": MESSY_SOURCE, "_loaded_parts": list(CAR_PARTS),
               "_project_dir": "/p"}
        report = generate_quality_report(car, "Championship")
        assert report.passed is False
        assert len(report.blocking_violations) > 0
        # Should have actionable feedback
        combined = " ".join(report.blocking_violations)
        assert "reliability" in combined.lower() or "complexity" in combined.lower()

    def test_no_source_defaults_to_pass(self):
        """Car without _source gets a passing report with default reliability."""
        car = {"_loaded_parts": ["gearbox"]}
        report = generate_quality_report(car, "F1")
        assert report.passed is True
        assert report.reliability_score == 1.0
