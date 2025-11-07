import os
from unittest.mock import Mock

import pytest

# Set test environment BEFORE importing app modules
os.environ["DOTENV_FILE"] = ".env.test"

# Import auth module after environment setup
from auth import auth as auth_module


def _make_response(status_code, json_data=None):
    response = Mock()
    response.status_code = status_code
    response.json = Mock(return_value=json_data or {})
    response.raise_for_status = Mock()
    return response


def test_reuses_refreshed_session_for_concurrent_requests(monkeypatch):
    """Ensure concurrent requests reuse refreshed sealed sessions."""
    # Reset caches before the test
    auth_module._session_validation_cache.clear()
    auth_module._session_refresh_cache.clear()

    validation_payload = {
        "user": {"id": "user-123", "email": "user@example.com"},
        "organization_id": "org_123",
        "role": "member",
    }

    validate_calls = []

    def fake_get(url, headers=None, timeout=10):
        validate_calls.append(headers["Authorization"] if headers else None)

        # First call is for the stale session and should return 401
        if len(validate_calls) == 1:
            assert headers["Authorization"] == "Bearer OLD_SESSION"
            return _make_response(401)

        # Second call validates the newly refreshed session
        if len(validate_calls) == 2:
            assert headers["Authorization"] == "Bearer NEW_SESSION"
            return _make_response(200, validation_payload)

        pytest.fail("Unexpected validation request")

    def fake_post(url, json=None, headers=None, timeout=10):
        assert json == {"sealed_session": "OLD_SESSION"}
        return _make_response(200, {"sealed_session": "NEW_SESSION"})

    # Patch requests in the auth_module's namespace
    monkeypatch.setattr("auth.auth.requests.get", fake_get)
    monkeypatch.setattr("auth.auth.requests.post", fake_post)

    # First authentication refreshes the session
    auth_response, refreshed = auth_module._authenticate_session("OLD_SESSION")
    assert refreshed is True, f"Expected refreshed=True but got {refreshed}"
    assert auth_response.sealed_session == "NEW_SESSION"
    assert len(validate_calls) == 2

    # Second authentication should reuse cached refresh without hitting the proxy
    auth_response_2, refreshed_2 = auth_module._authenticate_session("OLD_SESSION")
    assert refreshed_2 is True
    assert auth_response_2.sealed_session == "NEW_SESSION"
    assert len(validate_calls) == 2  # No additional proxy calls


def test_logout_clears_all_caches(monkeypatch):
    """Ensure logout clears both validation and refresh caches."""

    # Reset and populate caches
    auth_module._session_validation_cache.clear()
    auth_module._session_refresh_cache.clear()

    # Add some test data to both caches
    auth_module._session_validation_cache["test_key_1"] = {"data": "test"}
    auth_module._session_refresh_cache["test_key_2"] = {"data": "test"}

    assert len(auth_module._session_validation_cache) == 1
    assert len(auth_module._session_refresh_cache) == 1

    # Clear all caches
    auth_module._clear_all_session_caches()

    # Verify both caches are empty
    assert len(auth_module._session_validation_cache) == 0
    assert len(auth_module._session_refresh_cache) == 0
