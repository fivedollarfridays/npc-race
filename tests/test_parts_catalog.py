"""Tests for parts catalog (T20.1 + T20.3)."""

from engine.parts_catalog import (
    CATALOG, BUDGET_CAP, DEFAULTS,
    get_component, get_defaults, list_components, list_categories,
    get_total_cost, validate_build, validate_budget,
)


class TestCatalogStructure:
    def test_all_categories_exist(self):
        assert len(CATALOG) == 9

    def test_each_category_has_options(self):
        for cat, options in CATALOG.items():
            assert len(options) >= 2, f"{cat} has < 2 options"

    def test_defaults_valid(self):
        defaults = get_defaults()
        for cat, comp_id in defaults.items():
            assert get_component(cat, comp_id) is not None, f"Default {comp_id} not found"

    def test_get_component(self):
        comp = get_component("ENGINE", "pu_balanced")
        assert comp is not None
        assert "hp" in comp
        assert "cost_m" in comp

    def test_list_components(self):
        engines = list_components("ENGINE")
        assert len(engines) >= 2
        assert "pu_balanced" in engines

    def test_list_categories(self):
        cats = list_categories()
        assert len(cats) == 9

    def test_budget_cap_constant(self):
        assert BUDGET_CAP == 140

    def test_component_has_required_fields(self):
        for cat, options in CATALOG.items():
            for comp_id, comp in options.items():
                assert "name" in comp, f"{cat}/{comp_id} missing name"
                assert "cost_m" in comp, f"{cat}/{comp_id} missing cost_m"


class TestBudgetValidation:
    def test_defaults_under_budget(self):
        cost = get_total_cost(DEFAULTS)
        assert cost <= BUDGET_CAP

    def test_all_expensive_over_budget(self):
        expensive = {}
        for cat, options in CATALOG.items():
            most = max(options.items(), key=lambda x: x[1].get("cost_m", 0))
            expensive[cat] = most[0]
        cost = get_total_cost(expensive)
        assert cost > BUDGET_CAP

    def test_missing_category_invalid(self):
        partial = dict(DEFAULTS)
        del partial["ENGINE"]
        valid, msg = validate_build(partial)
        assert not valid
        assert "Missing" in msg

    def test_invalid_component_id(self):
        bad = dict(DEFAULTS)
        bad["ENGINE"] = "nonexistent"
        valid, msg = validate_build(bad)
        assert not valid

    def test_validate_returns_cost(self):
        under, cost = validate_budget(DEFAULTS)
        assert under is True
        assert cost > 0
