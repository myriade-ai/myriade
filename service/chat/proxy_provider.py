import logging
import threading
from typing import Any, Dict, Optional

import anthropic
from agentlys.base import AgentlysBase
from agentlys.providers.anthropic import AnthropicProvider
from anthropic._types import Omit
from flask import g, has_request_context
from flask import session as flask_session

from auth.auth import (
    UnauthorizedError,
    _authenticate_session,
    _invalidate_session_cache,
)
from config import INFRA_URL

logger = logging.getLogger(__name__)

# Thread-local storage for response data
_thread_local = threading.local()


def get_last_response_data(key: str) -> Optional[Any]:
    """Get data from the last AI response."""
    return getattr(_thread_local, key, None)


# Store the original method
_original_create = anthropic.resources.Messages.create


def patched_create(self, **kwargs):
    """Monkey patch to intercept messages.create() responses."""
    # Call the original method
    response = _original_create(self, **kwargs)

    try:
        # The credits info is directly on the response object!
        if hasattr(response, "_credits_remaining"):
            logger.info(f"Intercepted credits: {response._credits_remaining}")
            _thread_local.credits_remaining = response._credits_remaining

    except Exception as e:
        logger.warning(f"Error extracting response data: {e}")

    return response


# Apply the monkey patch
anthropic.resources.Messages.create = patched_create


class ProxyProvider(AnthropicProvider):
    """Custom agentlys provider that routes requests through our AI proxy."""

    def __init__(self, chat: AgentlysBase, model: str):
        self.model = model
        self.chat = chat
        super().__init__(chat, model)
        self.client.base_url = f"{INFRA_URL}/ai"

    def _get_current_session(self):
        """Get session cookie from current context"""
        if hasattr(g, "sealed_session"):
            return g.sealed_session  # HTTP context
        else:
            return flask_session.get("sealed_session")  # Socket context

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers from current session."""
        headers = {"Content-Type": "application/json"}

        # Always call _authenticate_session - it handles caching internally
        session_cookie = self._get_current_session()
        if not session_cookie:
            raise Exception("No session cookie found")

        try:
            auth_response, is_refreshed = _authenticate_session(session_cookie)

            # Update session in current context if refreshed
            if is_refreshed:
                if has_request_context():
                    g.sealed_session = auth_response.sealed_session
                else:
                    flask_session["sealed_session"] = auth_response.sealed_session

            # Use the current sealed session (refreshed or cached)
            headers["Authorization"] = f"Bearer {auth_response.sealed_session}"

        except UnauthorizedError as e:
            raise Exception("Authentication failed") from e

        headers["X-Api-Key"] = Omit()  # type: ignore
        return headers

    async def fetch_async(self, **kwargs):
        # Build headers with the current session
        headers = self._get_auth_headers()
        kwargs["extra_headers"] = headers

        try:
            return await super().fetch_async(**kwargs)
        except anthropic.AuthenticationError as exc:
            # The AI proxy can respond with INVALID_JWT if the cached sealed
            # session is no longer valid (e.g., revoked). Clear caches and retry
            # once with a freshly validated session.
            error_message = str(exc)
            if exc.status_code == 401 or "INVALID_JWT" in error_message:
                logger.warning("AI proxy rejected session (INVALID_JWT), retrying")

                current_session = self._get_current_session()
                if current_session:
                    _invalidate_session_cache(current_session)

                # Retry with a fresh authentication
                refreshed_headers = self._get_auth_headers()
                kwargs["extra_headers"] = refreshed_headers
                return await super().fetch_async(**kwargs)

            raise
