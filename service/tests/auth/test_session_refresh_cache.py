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


def test_invalidate_session_clears_specific_session_and_reverse_mappings():
    """
    Ensure invalidating a session clears:
    1. The session from validation cache
    2. The session from refresh cache (as a key)
    3. Any reverse mappings (old_session → this_session)
    4. Does NOT clear other unrelated sessions
    """
    import hashlib

    # Reset caches
    auth_module._session_validation_cache.clear()
    auth_module._session_refresh_cache.clear()

    # Create test sessions
    session_to_logout = "SESSION_TO_LOGOUT"
    old_session = "OLD_SESSION_THAT_WAS_REFRESHED"
    unrelated_session = "UNRELATED_SESSION"

    # Hash the sessions as the cache does
    logout_hash = hashlib.sha256(session_to_logout.encode()).hexdigest()[:32]
    old_hash = hashlib.sha256(old_session.encode()).hexdigest()[:32]
    unrelated_hash = hashlib.sha256(unrelated_session.encode()).hexdigest()[:32]

    # Populate caches
    # 1. Validation cache entries
    auth_module._session_validation_cache[logout_hash] = {"user": "test"}
    auth_module._session_validation_cache[unrelated_hash] = {"user": "other"}

    # 2. Refresh cache: old_session was refreshed to session_to_logout
    auth_module._session_refresh_cache[old_hash] = {
        "sealed_session": session_to_logout,
        "validation_data": {"user": "test"},
        "expires": 9999999999,
    }

    # 3. Another unrelated refresh mapping
    auth_module._session_refresh_cache["another_old"] = {
        "sealed_session": unrelated_session,
        "validation_data": {"user": "other"},
        "expires": 9999999999,
    }

    # Verify setup
    assert len(auth_module._session_validation_cache) == 2
    assert len(auth_module._session_refresh_cache) == 2

    # Invalidate the session being logged out
    auth_module._invalidate_session_cache(session_to_logout)

    # Verify results:
    # 1. session_to_logout removed from validation cache
    assert logout_hash not in auth_module._session_validation_cache

    # 2. The reverse mapping (old_session → session_to_logout) removed
    assert old_hash not in auth_module._session_refresh_cache

    # 3. Unrelated sessions remain intact
    assert unrelated_hash in auth_module._session_validation_cache
    assert "another_old" in auth_module._session_refresh_cache
    another_old_entry = auth_module._session_refresh_cache["another_old"]
    assert another_old_entry["sealed_session"] == unrelated_session

    # Final cache sizes
    assert len(auth_module._session_validation_cache) == 1
    assert len(auth_module._session_refresh_cache) == 1
