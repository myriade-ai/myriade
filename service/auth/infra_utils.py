"""
Utility functions for making authenticated requests to the auth proxy
"""

import requests
from flask import g

from config import INFRA_URL, USE_LOCAL_AUTH


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
    # Local development mode: return mock responses
    if USE_LOCAL_AUTH:
        # Create a mock response object
        mock_response = requests.Response()
        mock_response.status_code = 200

        # Handle different endpoints
        if endpoint == "/user/credits":
            mock_data = {
                "credits": 999999,
                "unlimited": True,
            }
        else:
            mock_data = {"status": "ok", "message": "Local dev mode"}

        mock_response._content = str(mock_data).encode()
        mock_response.json = lambda: mock_data
        return mock_response

    # Get session cookie (sealed session)
    session_cookie = g.sealed_session
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
    # Local development mode: return mock organization data
    if USE_LOCAL_AUTH:
        return {
            "id": organization_id,
            "name": f"Dev Organization ({organization_id})",
        }

    response = make_authenticated_proxy_request(f"/organizations/{organization_id}")
    response.raise_for_status()
    return response.json()
