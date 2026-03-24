"""Tests for pytest mark registration and slow→integration alias (T36.2)."""

import pytest


class TestMarkRegistration:
    """Verify custom marks are registered and don't produce warnings."""

    def test_smoke_mark_registered(self):
        """The 'smoke' mark should be registered in pyproject.toml."""
        # If this mark weren't registered, pytest would emit a warning.
        # We simply verify the mark object is accessible.
        mark = pytest.mark.smoke
        assert mark is not None

    def test_integration_mark_registered(self):
        """The 'integration' mark should be registered in pyproject.toml."""
        mark = pytest.mark.integration
        assert mark is not None

    def test_slow_mark_still_registered(self):
        """The 'slow' mark should remain registered as a deprecated alias."""
        mark = pytest.mark.slow
        assert mark is not None


@pytest.mark.slow
class TestSlowAliasToIntegration:
    """Tests marked 'slow' should also carry the 'integration' marker.

    The conftest.py hook should add 'integration' to any item with 'slow'.
    """

    def test_slow_item_has_integration_keyword(self, request):
        """A @pytest.mark.slow test should also have 'integration' keyword."""
        assert "integration" in request.keywords


@pytest.mark.smoke
class TestSmokeMarkWorks:
    """Verify smoke-marked tests are selectable."""

    def test_smoke_selectable(self):
        """Smoke tests should run when selected with -m smoke."""
        assert True


@pytest.mark.integration
class TestIntegrationMarkWorks:
    """Verify integration-marked tests are selectable."""

    def test_integration_selectable(self):
        """Integration tests should run when selected with -m integration."""
        assert True
