import asyncio

import anthropic
import httpx

from chat.proxy_provider import ProxyProvider


def test_fetch_async_retries_on_invalid_jwt(monkeypatch):
    provider = ProxyProvider.__new__(ProxyProvider)

    # First request raises INVALID_JWT, second succeeds
    call_headers = []

    async def fake_super_fetch(self, **kwargs):
        call_headers.append(kwargs.get("extra_headers"))
        if len(call_headers) == 1:
            response = httpx.Response(
                401, request=httpx.Request("GET", "https://example.com")
            )
            raise anthropic.AuthenticationError(
                message=(
                    "Error code: 401 - {'error': 'Authentication failed: "
                    "AuthenticateWithSessionCookieFailureReason.INVALID_JWT'}"
                ),
                response=response,
                body=None,
            )
        return "ok"

    headers_iter = iter(
        [
            {"Authorization": "Bearer OLD_SESSION"},
            {"Authorization": "Bearer NEW_SESSION"},
        ]
    )

    monkeypatch.setattr(
        ProxyProvider, "_get_auth_headers", lambda self: next(headers_iter)
    )
    monkeypatch.setattr(
        ProxyProvider, "_get_current_session", lambda self: "OLD_SESSION"
    )
    monkeypatch.setattr(
        "chat.proxy_provider.AnthropicProvider.fetch_async", fake_super_fetch
    )

    invalidated_sessions = []

    def fake_invalidate(session):
        invalidated_sessions.append(session)

    monkeypatch.setattr(
        "chat.proxy_provider._invalidate_session_cache", fake_invalidate
    )

    result = asyncio.run(provider.fetch_async())

    assert result == "ok"
    assert invalidated_sessions == ["OLD_SESSION"]
    assert call_headers == [
        {"Authorization": "Bearer OLD_SESSION"},
        {"Authorization": "Bearer NEW_SESSION"},
    ]
