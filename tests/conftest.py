"""Shared pytest fixtures and mark configuration for NPC Race tests."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Treat 'slow' as a deprecated alias for 'integration'."""
    integration = pytest.mark.integration
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(integration)


@pytest.fixture
def sample_cars():
    """Pre-built car dicts matching engine.car_loader format."""
    from tests.fixtures.race_data import SAMPLE_CARS
    return list(SAMPLE_CARS)


@pytest.fixture
def sample_results():
    """Pre-built race results matching engine.replay.get_results format."""
    from tests.fixtures.race_data import SAMPLE_RESULTS
    return list(SAMPLE_RESULTS)


@pytest.fixture
def sample_lap_summaries():
    """Pre-built lap summaries matching engine.lap_accumulator format."""
    from tests.fixtures.race_data import SAMPLE_LAP_SUMMARIES
    return dict(SAMPLE_LAP_SUMMARIES)


@pytest.fixture
def sample_results_summary():
    """Pre-built results summary matching engine.results format."""
    from tests.fixtures.race_data import SAMPLE_RESULTS_SUMMARY
    return dict(SAMPLE_RESULTS_SUMMARY)
