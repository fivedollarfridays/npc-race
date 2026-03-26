"""Tests for engine/coaching.py — coaching tips from trial efficiency data."""

from engine.time_trial import TrialResult


def _make_result(**eff_overrides: float) -> TrialResult:
    """Helper: build a TrialResult with custom efficiency values."""
    efficiency = {"gearbox": 1.0, "cooling": 1.0, "fuel_mix": 1.0}
    efficiency.update(eff_overrides)
    return TrialResult(
        lap_time=92.456,
        sector_times=[30.1, 31.2, 31.156],
        efficiency=efficiency,
        car_name="TestCar",
        track_name="monza",
    )


# --- Cycle 1: gearbox tip ---


def test_gearbox_tip_when_low():
    result = _make_result(gearbox=0.90)
    from engine.coaching import generate_coaching

    tips = generate_coaching(result)
    assert any("peak torque" in t.lower() for t in tips)
    assert any("90%" in t for t in tips)


# --- Cycle 2: cooling tip ---


def test_cooling_tip_when_low():
    result = _make_result(cooling=0.85)
    from engine.coaching import generate_coaching

    tips = generate_coaching(result)
    assert any("drag" in t.lower() for t in tips)
    assert any("85%" in t for t in tips)


# --- Cycle 3: no tips when optimal ---


def test_no_tips_when_optimal():
    result = _make_result(gearbox=0.98, cooling=0.95, fuel_mix=0.96)
    from engine.coaching import generate_coaching

    tips = generate_coaching(result)
    assert len(tips) == 1
    assert "excellent" in tips[0].lower()


# --- Cycle 4: combined loss shown ---


def test_combined_loss_shown():
    result = _make_result(gearbox=0.90, cooling=0.85, fuel_mix=0.88)
    from engine.coaching import generate_coaching

    tips = generate_coaching(result)
    combined_tips = [t for t in tips if "combined" in t.lower()]
    assert len(combined_tips) == 1
    assert "losing" in combined_tips[0].lower()


# --- Cycle 5: fuel mix tip ---


def test_fuel_mix_tip_when_low():
    result = _make_result(fuel_mix=0.85)
    from engine.coaching import generate_coaching

    tips = generate_coaching(result)
    assert any("fuel mix" in t.lower() for t in tips)
    assert any("lambda" in t.lower() for t in tips)


# --- Cycle 6: format_trial_output ---


def test_format_trial_output():
    result = _make_result(gearbox=0.92, cooling=0.97)
    from engine.coaching import format_trial_output, generate_coaching

    tips = generate_coaching(result)
    output = format_trial_output(result, tips)
    assert "MONZA" in output
    assert "1:32" in output
    assert "Gearbox" in output
    assert "Cooling" in output


def test_format_includes_tips():
    result = _make_result(gearbox=0.88)
    from engine.coaching import format_trial_output, generate_coaching

    tips = generate_coaching(result)
    output = format_trial_output(result, tips)
    assert "Tip:" in output
    assert "peak torque" in output.lower()
