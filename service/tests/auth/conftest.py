"""
Local conftest for auth tests.

This overrides the parent conftest's mock_auth fixture to allow testing
the actual authentication implementation without mocks.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def mock_auth():
    """Override parent mock_auth fixture - do not mock for these tests."""
    # Just yield without any mocking
    yield
