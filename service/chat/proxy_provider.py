import logging
import threading
from typing import Any, Dict, Optional

import anthropic
from autochat.base import AutochatBase
from autochat.providers.anthropic import AnthropicProvider
from flask import has_request_context, request

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
    """Custom autochat provider that routes requests through our AI proxy."""

    def __init__(self, chat: AutochatBase, model: str):
        self.model = model
        self.chat = chat
        super().__init__(chat, model)
        self.client.base_url = f"{INFRA_URL}/ai"

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers from current session."""
        headers = {"Content-Type": "application/json"}

        if not has_request_context():
            raise Exception("No Flask request context available")

        session_cookie = request.cookies.get("session")
        if not session_cookie:
            raise Exception("No session cookie found in request")
        headers["Authorization"] = f"Bearer {session_cookie}"
        from anthropic._types import Omit

        headers["X-Api-Key"] = Omit()  # type: ignore
        return headers

    async def fetch_async(self, **kwargs):
        headers = self._get_auth_headers()
        kwargs["extra_headers"] = headers
        return await super().fetch_async(**kwargs)
