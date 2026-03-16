"""Tests for car_template.py — verify it's importable and well-formed."""

import importlib
import sys
import types


def _import_car_template() -> types.ModuleType:
    """Import car_template from project root."""
    if "car_template" in sys.modules:
        del sys.modules["car_template"]
    return importlib.import_module("car_template")


def test_car_template_imports_cleanly():
    """car_template.py must be importable without errors."""
    mod = _import_car_template()
    assert mod is not None


def test_car_template_has_required_constants():
    """Template must export CAR_NAME, CAR_COLOR, and stat constants."""
    mod = _import_car_template()
    assert isinstance(mod.CAR_NAME, str)
    assert isinstance(mod.CAR_COLOR, str)
    for stat in ("POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"):
        assert hasattr(mod, stat), f"Missing stat: {stat}"
        assert isinstance(getattr(mod, stat), (int, float))


def test_car_template_budget_within_100():
    """Default stats must not exceed the 100-point budget."""
    mod = _import_car_template()
    total = mod.POWER + mod.GRIP + mod.WEIGHT + mod.AERO + mod.BRAKES
    assert total <= 100, f"Budget exceeded: {total}"


def test_car_template_strategy_callable():
    """strategy() must be a callable function."""
    mod = _import_car_template()
    assert callable(mod.strategy)


def test_car_template_strategy_returns_valid_dict():
    """strategy() must return a dict with throttle, boost, tire_mode."""
    mod = _import_car_template()
    fake_state = {
        "speed": 100.0,
        "position": 1,
        "total_cars": 4,
        "lap": 1,
        "total_laps": 3,
        "tire_wear": 0.2,
        "boost_available": True,
        "boost_active": False,
        "curvature": 0.01,
        "nearby_cars": [],
        "distance": 500.0,
        "track_length": 1000.0,
        "lateral": 0.0,
    }
    result = mod.strategy(fake_state)
    assert isinstance(result, dict)
    assert "throttle" in result
    assert "boost" in result
    assert "tire_mode" in result
    assert 0.0 <= result["throttle"] <= 1.0
    assert result["tire_mode"] in ("conserve", "balanced", "push")


def test_car_template_under_200_lines():
    """Template must stay under 200 lines."""
    import pathlib

    template_path = pathlib.Path(__file__).parent.parent / "car_template.py"
    line_count = len(template_path.read_text().splitlines())
    assert line_count < 200, f"car_template.py is {line_count} lines (limit: 200)"


def test_car_template_docstring_documents_all_state_fields():
    """Docstring must mention every strategy state field."""
    mod = _import_car_template()
    doc = mod.__doc__
    assert doc is not None, "Module docstring is missing"
    required_fields = [
        "speed", "position", "total_cars", "lap", "total_laps",
        "tire_wear", "boost_available", "boost_active", "curvature",
        "nearby_cars", "distance", "track_length", "lateral",
    ]
    for field in required_fields:
        assert field in doc, f"Docstring missing field: {field}"


def test_car_template_docstring_documents_return_keys():
    """Docstring must mention all valid return keys."""
    mod = _import_car_template()
    doc = mod.__doc__
    required_keys = ["throttle", "boost", "tire_mode"]
    for key in required_keys:
        assert key in doc, f"Docstring missing return key: {key}"


def test_car_template_docstring_documents_tire_modes():
    """Docstring must mention all three valid tire modes."""
    mod = _import_car_template()
    doc = mod.__doc__
    for mode in ("conserve", "balanced", "push"):
        assert mode in doc, f"Docstring missing tire mode: {mode}"


def test_car_template_docstring_has_field_types():
    """Docstring must document types for key strategy state fields."""
    mod = _import_car_template()
    doc = mod.__doc__
    # Should mention float for numeric fields and bool for boolean fields
    assert "float" in doc.lower() or "0.0" in doc, "Docstring should show numeric ranges"
    assert "bool" in doc.lower() or "True" in doc, "Docstring should show boolean types"


def test_car_template_has_example_strategies():
    """Template source should include commented example strategy patterns."""
    import pathlib

    template_path = pathlib.Path(__file__).parent.parent / "car_template.py"
    source = template_path.read_text()
    # Must have labeled example strategy sections
    assert "EXAMPLE" in source.upper() or "Example" in source
    # Should have at least 2 distinct strategy pattern names
    patterns_found = sum(1 for p in ["defensive", "aggressive", "draft"]
                         if p in source.lower())
    assert patterns_found >= 2, (
        f"Need at least 2 example strategy patterns, found {patterns_found}"
    )


def test_car_template_documents_nearby_cars_fields():
    """Docstring must document all nearby_cars entry fields."""
    mod = _import_car_template()
    doc = mod.__doc__
    for field in ("name", "distance_ahead", "speed", "lateral"):
        assert field in doc, f"Docstring missing nearby_cars field: {field}"


def test_car_template_documents_budget_rule():
    """Docstring must clearly state the 100-point budget rule."""
    mod = _import_car_template()
    doc = mod.__doc__
    assert "100" in doc, "Docstring must mention 100-point budget"
