import hashlib
import time

import pytest
import requests

from auth.auth import (
    SealedSessionAuthResponse,
    _authenticate_session,
    _cache_session_validation,
    _invalidate_session_cache,
    _session_validation_cache,
)


class MockResponse:
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


@pytest.fixture(autouse=True)
def clear_session_cache():
    """Ensure cache is cleared before and after each test."""
    _session_validation_cache.clear()
    yield
    _session_validation_cache.clear()


def expire_cache_entry(session_cookie):
    cache_key = hashlib.sha256(session_cookie.encode()).hexdigest()[:32]
    _session_validation_cache[cache_key]["expires"] = time.time() - 10


def test_refresh_uses_cached_refresh_token(monkeypatch):
    session_cookie = "expired_session_token"
    validation_payload = {
        "user": {"id": "user_123"},
        "refresh_token": "refresh_token_value",
    }

    _cache_session_validation(session_cookie, validation_payload, ttl_minutes=0.001)
    expire_cache_entry(session_cookie)

    # Track payload sent to refresh endpoint
    captured_payload = {}

    def mock_get(url, headers=None, timeout=None):
        assert url.endswith("/auth/validate")
        auth_header = headers.get("Authorization")

        if auth_header == f"Bearer {session_cookie}":
            return MockResponse(
                401,
                {
                    "reason": "AuthenticateWithSessionCookieFailureReason.INVALID_JWT",
                },
            )

        assert auth_header == "Bearer new_session_token"
        return MockResponse(
            200,
            {
                "user": {"id": "user_123"},
                "refresh_token": "new_refresh_token",
            },
        )

    def mock_post(url, json=None, headers=None, timeout=None):
        assert url.endswith("/auth/refresh")
        captured_payload.update(json)
        return MockResponse(200, {"sealed_session": "new_session_token"})

    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(requests, "post", mock_post)

    auth_response, refreshed = _authenticate_session(session_cookie)

    assert refreshed is True
    assert isinstance(auth_response, SealedSessionAuthResponse)
    assert auth_response.sealed_session == "new_session_token"
    assert captured_payload == {
        "sealed_session": session_cookie,
        "refresh_token": "refresh_token_value",
    }

    # Cleanup cached entries for new session
    _invalidate_session_cache("new_session_token")
