"""Tests that shared test fixtures match real simulation output formats."""


# -- Keys expected in each data structure (derived from engine source) --

CAR_REQUIRED_KEYS = {
    "CAR_NAME", "CAR_COLOR", "POWER", "GRIP", "WEIGHT", "AERO", "BRAKES",
    "reliability_score",
}

RESULT_REQUIRED_KEYS = {
    "name", "position", "total_time_s", "best_lap_s",
    "lap_times", "finished", "reliability_score",
}

SUMMARY_REQUIRED_KEYS = {"track", "laps", "league", "cars", "integrity"}

SUMMARY_CAR_REQUIRED_KEYS = {
    "name", "position", "total_time_s", "best_lap_s", "reliability_score",
}

LAP_ENTRY_REQUIRED_KEYS = {
    "lap", "time_s", "position", "tire_compound", "tire_wear",
    "pit_stop", "fuel_remaining_pct",
}

GRID_REQUIRED_KEYS = {"name", "qualifying_time", "grid_position"}


# ---- Cycle 1: SAMPLE_CARS structure ----


class TestSampleCars:
    def test_importable(self):
        from tests.fixtures.race_data import SAMPLE_CARS
        assert isinstance(SAMPLE_CARS, list)

    def test_has_at_least_two_cars(self):
        from tests.fixtures.race_data import SAMPLE_CARS
        assert len(SAMPLE_CARS) >= 2

    def test_car_has_required_keys(self):
        from tests.fixtures.race_data import SAMPLE_CARS
        for car in SAMPLE_CARS:
            missing = CAR_REQUIRED_KEYS - set(car.keys())
            assert not missing, f"{car.get('CAR_NAME', '?')} missing: {missing}"

    def test_car_color_is_hex(self):
        import re
        from tests.fixtures.race_data import SAMPLE_CARS
        for car in SAMPLE_CARS:
            assert re.fullmatch(r"#[0-9a-fA-F]{6}", car["CAR_COLOR"])

    def test_stat_budget_within_limit(self):
        from tests.fixtures.race_data import SAMPLE_CARS
        stat_fields = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]
        for car in SAMPLE_CARS:
            total = sum(car[f] for f in stat_fields)
            assert total <= 100, f"{car['CAR_NAME']} budget {total} > 100"


# ---- Cycle 2: SAMPLE_RESULTS structure ----


class TestSampleResults:
    def test_importable(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS
        assert isinstance(SAMPLE_RESULTS, list)

    def test_has_required_keys(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS
        for r in SAMPLE_RESULTS:
            missing = RESULT_REQUIRED_KEYS - set(r.keys())
            assert not missing, f"Result for {r.get('name', '?')} missing: {missing}"

    def test_positions_are_sequential(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS
        positions = [r["position"] for r in SAMPLE_RESULTS]
        assert positions == list(range(1, len(SAMPLE_RESULTS) + 1))

    def test_lap_times_is_list(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS
        for r in SAMPLE_RESULTS:
            assert isinstance(r["lap_times"], list)
            assert all(isinstance(t, float) for t in r["lap_times"])

    def test_total_time_is_sum_of_lap_times(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS
        for r in SAMPLE_RESULTS:
            if r["finished"] and r["lap_times"]:
                assert abs(r["total_time_s"] - sum(r["lap_times"])) < 0.01


# ---- Cycle 3: SAMPLE_RESULTS_SUMMARY structure ----


class TestSampleResultsSummary:
    def test_importable(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS_SUMMARY
        assert isinstance(SAMPLE_RESULTS_SUMMARY, dict)

    def test_has_required_keys(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS_SUMMARY
        missing = SUMMARY_REQUIRED_KEYS - set(SAMPLE_RESULTS_SUMMARY.keys())
        assert not missing, f"Summary missing: {missing}"

    def test_cars_have_required_keys(self):
        from tests.fixtures.race_data import SAMPLE_RESULTS_SUMMARY
        for car in SAMPLE_RESULTS_SUMMARY["cars"]:
            missing = SUMMARY_CAR_REQUIRED_KEYS - set(car.keys())
            assert not missing, f"Summary car {car.get('name', '?')} missing: {missing}"


# ---- Cycle 4: SAMPLE_LAP_SUMMARIES structure ----


class TestSampleLapSummaries:
    def test_importable(self):
        from tests.fixtures.race_data import SAMPLE_LAP_SUMMARIES
        assert isinstance(SAMPLE_LAP_SUMMARIES, dict)

    def test_entries_have_required_keys(self):
        from tests.fixtures.race_data import SAMPLE_LAP_SUMMARIES
        for car_name, laps in SAMPLE_LAP_SUMMARIES.items():
            assert isinstance(laps, list), f"{car_name} laps is not a list"
            for entry in laps:
                missing = LAP_ENTRY_REQUIRED_KEYS - set(entry.keys())
                assert not missing, f"{car_name} lap entry missing: {missing}"

    def test_fuel_remaining_is_fraction(self):
        from tests.fixtures.race_data import SAMPLE_LAP_SUMMARIES
        for car_name, laps in SAMPLE_LAP_SUMMARIES.items():
            for entry in laps:
                assert 0.0 <= entry["fuel_remaining_pct"] <= 1.0


# ---- Cycle 5: SAMPLE_GRID structure ----


class TestSampleGrid:
    def test_importable(self):
        from tests.fixtures.race_data import SAMPLE_GRID
        assert isinstance(SAMPLE_GRID, list)

    def test_entries_have_required_keys(self):
        from tests.fixtures.race_data import SAMPLE_GRID
        for entry in SAMPLE_GRID:
            missing = GRID_REQUIRED_KEYS - set(entry.keys())
            assert not missing, f"Grid entry missing: {missing}"


# ---- Cycle 6: Factory functions ----


class TestMakeResults:
    def test_default_produces_six_cars(self):
        from tests.fixtures.race_data import make_results
        results = make_results()
        assert len(results) == 6

    def test_custom_size(self):
        from tests.fixtures.race_data import make_results
        results = make_results(n_cars=3, n_laps=5)
        assert len(results) == 3
        for r in results:
            assert len(r["lap_times"]) == 5

    def test_result_keys_match(self):
        from tests.fixtures.race_data import make_results
        for r in make_results(n_cars=2, n_laps=2):
            missing = RESULT_REQUIRED_KEYS - set(r.keys())
            assert not missing, f"make_results missing: {missing}"

    def test_positions_sequential(self):
        from tests.fixtures.race_data import make_results
        results = make_results(n_cars=4)
        positions = [r["position"] for r in results]
        assert positions == [1, 2, 3, 4]

    def test_total_time_is_sum(self):
        from tests.fixtures.race_data import make_results
        for r in make_results(n_cars=3, n_laps=4):
            assert abs(r["total_time_s"] - sum(r["lap_times"])) < 0.01


class TestMakeLapSummaries:
    def test_default_produces_six_cars(self):
        from tests.fixtures.race_data import make_lap_summaries
        summaries = make_lap_summaries()
        assert len(summaries) == 6

    def test_custom_size(self):
        from tests.fixtures.race_data import make_lap_summaries
        summaries = make_lap_summaries(n_cars=2, n_laps=4)
        assert len(summaries) == 2
        for laps in summaries.values():
            assert len(laps) == 4

    def test_entry_keys_match(self):
        from tests.fixtures.race_data import make_lap_summaries
        for car_name, laps in make_lap_summaries(n_cars=2, n_laps=2).items():
            for entry in laps:
                missing = LAP_ENTRY_REQUIRED_KEYS - set(entry.keys())
                assert not missing, f"{car_name} entry missing: {missing}"

    def test_fuel_decreases_over_laps(self):
        from tests.fixtures.race_data import make_lap_summaries
        for car_name, laps in make_lap_summaries(n_cars=1, n_laps=5).items():
            fuels = [e["fuel_remaining_pct"] for e in laps]
            assert fuels == sorted(fuels, reverse=True), "fuel should decrease"


# ---- Cycle 7: conftest fixtures ----


class TestConftestFixtures:
    def test_sample_results_fixture(self, sample_results):
        assert isinstance(sample_results, list)
        assert len(sample_results) >= 2

    def test_sample_lap_summaries_fixture(self, sample_lap_summaries):
        assert isinstance(sample_lap_summaries, dict)
        assert len(sample_lap_summaries) >= 2

    def test_sample_cars_fixture(self, sample_cars):
        assert isinstance(sample_cars, list)
        assert len(sample_cars) >= 2

    def test_sample_results_summary_fixture(self, sample_results_summary):
        assert isinstance(sample_results_summary, dict)
        assert "cars" in sample_results_summary
