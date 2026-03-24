"""Tests for CI workflow structure — validates tiered test execution."""

import os

import yaml

CI_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".github",
    "workflows",
    "ci.yml",
)


def _load_ci():
    with open(CI_PATH) as f:
        return yaml.safe_load(f)


def test_ci_has_required_jobs():
    ci = _load_ci()
    jobs = set(ci["jobs"].keys())
    expected = {"lint", "test-unit", "test-smoke", "test-integration", "validate-cars"}
    assert expected == jobs, f"Expected jobs {expected}, got {jobs}"


def test_old_jobs_removed():
    ci = _load_ci()
    jobs = ci["jobs"].keys()
    assert "test-fast" not in jobs, "test-fast should be replaced by test-unit + test-smoke"
    assert "test-full" not in jobs, "test-full should be replaced by test-integration"


def test_unit_tests_exclude_smoke_and_integration():
    ci = _load_ci()
    unit_steps = ci["jobs"]["test-unit"]["steps"]
    run_step = [s for s in unit_steps if s.get("name") == "Run unit tests"][0]
    cmd = run_step["run"]
    assert "not smoke" in cmd
    assert "not integration" in cmd
    assert "not slow" in cmd
    assert "--timeout=10" in cmd


def test_smoke_tests_marker():
    ci = _load_ci()
    smoke_steps = ci["jobs"]["test-smoke"]["steps"]
    run_step = [s for s in smoke_steps if s.get("name") == "Run smoke tests"][0]
    cmd = run_step["run"]
    assert "-m smoke" in cmd
    assert "--timeout=30" in cmd


def test_integration_tests_marker_and_condition():
    ci = _load_ci()
    job = ci["jobs"]["test-integration"]
    # Only on labeled PRs
    assert "ready-to-merge" in job["if"]
    assert "pull_request" in job["if"]
    # Correct pytest command
    run_step = [s for s in job["steps"] if s.get("name") == "Run integration tests"][0]
    cmd = run_step["run"]
    assert "integration or slow" in cmd
    assert "--timeout=120" in cmd


def test_unit_and_smoke_have_no_needs():
    """Unit and smoke should run in parallel (no needs: dependency)."""
    ci = _load_ci()
    assert "needs" not in ci["jobs"]["test-unit"], "test-unit should not depend on other jobs"
    assert "needs" not in ci["jobs"]["test-smoke"], "test-smoke should not depend on other jobs"


def test_timeout_minutes():
    ci = _load_ci()
    assert ci["jobs"]["test-unit"]["timeout-minutes"] == 3
    assert ci["jobs"]["test-smoke"]["timeout-minutes"] == 8
    assert ci["jobs"]["test-integration"]["timeout-minutes"] == 20


def test_all_test_jobs_use_pip_cache():
    ci = _load_ci()
    for job_name in ("test-unit", "test-smoke", "test-integration"):
        steps = ci["jobs"][job_name]["steps"]
        cache_steps = [s for s in steps if s.get("uses", "").startswith("actions/cache")]
        assert len(cache_steps) == 1, f"{job_name} should have pip cache step"
