"""
Local conftest for auth tests.

This overrides the parent conftest's mock_auth fixture to allow testing
the actual authentication implementation without mocks.
"""

import pytest


@pytest.fixture(scope="function", autouse=True)
def no_auth_mock(monkeypatch):
    """
    Disable the global auth mock for these specific tests.

    The parent conftest patches auth.auth._authenticate_session, but we need
    to test the real implementation. We use monkeypatch to restore the original.
    """
    # Import the real function
    # Get the original function (before any mocks)
    # We need to reload the module to get the unmocked version
    import importlib

    from auth import auth

    importlib.reload(auth)

    yield
