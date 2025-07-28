"""
Utility functions for making authenticated requests to the auth proxy
"""

import requests
from flask import request

from config import INFRA_URL


def make_authenticated_proxy_request(endpoint, method="GET", **kwargs):
    """
    Make an authenticated request to the auth proxy using sealed session.

    Args:
        endpoint: The proxy endpoint (e.g., '/organizations/org_123')
        method: HTTP method (GET, POST, etc.)
        **kwargs: Additional arguments to pass to requests

    Returns:
        requests.Response object
    """
    # Get session cookie (sealed session)
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise ValueError("No session cookie found")

    try:
        # Use sealed session as Bearer token
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {session_cookie}"
        kwargs["headers"] = headers

        # Make request to proxy
        url = INFRA_URL + endpoint
        response = requests.request(method, url, **kwargs)
        return response

    except Exception as e:
        raise ValueError(f"Failed to make authenticated request: {str(e)}") from e


def get_organization_data(organization_id):
    """
    Get organization data from the proxy with proper authentication.

    Args:
        organization_id: The organization ID to fetch

    Returns:
        dict: Organization data

    Raises:
        requests.RequestException: If the request fails
        ValueError: If authentication fails
    """
    response = make_authenticated_proxy_request(f"/organizations/{organization_id}")
    response.raise_for_status()
    return response.json()
