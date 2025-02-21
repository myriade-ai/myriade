import base64
import hashlib
from functools import wraps
from typing import Union

from flask import g, jsonify, make_response, request
from workos import WorkOSClient
from workos.types.user_management.session import (
    AuthenticateWithSessionCookieErrorResponse,
    AuthenticateWithSessionCookieSuccessResponse,
)

from config import WORKOS_API_KEY, WORKOS_CLIENT_ID

workos_client = WorkOSClient(
    api_key=WORKOS_API_KEY,
    client_id=WORKOS_CLIENT_ID,
)

cookie_password = "mkPRI77h3M6iehoYFhwWXQ27f2sGpPuM"

# Generate a proper Fernet key from the password
cookie_password_bytes = cookie_password.encode()
cookie_password_b64 = base64.urlsafe_b64encode(
    hashlib.sha256(cookie_password_bytes).digest()
).decode("utf-8")


class UnauthorizedError(Exception):
    pass


def with_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate session cookie exists
        session_cookie = request.cookies.get("wos_session")
        if not session_cookie:
            return jsonify({"error": "No session cookie"}), 401

        # Load and authenticate session
        try:
            auth_response, is_refreshed = _authenticate_session(session_cookie)
        except UnauthorizedError as e:
            return jsonify({"error": str(e)}), 401

        # Set user context
        _set_user_context(auth_response)

        # Execute wrapped function
        res = f(*args, **kwargs)

        # Return response with refreshed session cookie if needed
        if is_refreshed:
            return _create_response_with_cookie(res, auth_response.sealed_session)
        return res

    return decorated_function


def _authenticate_session(
    session_cookie,
) -> tuple[AuthenticateWithSessionCookieSuccessResponse, bool]:
    """Authenticate and potentially refresh the session."""
    session = workos_client.user_management.load_sealed_session(
        sealed_session=session_cookie,
        cookie_password=cookie_password_b64,
    )

    auth_response = session.authenticate()
    if auth_response.authenticated:
        return auth_response, False  # type: ignore

    # Try refreshing the session
    refreshed_auth_response = session.refresh()
    if not refreshed_auth_response.authenticated:
        raise UnauthorizedError(refreshed_auth_response.reason)  # type: ignore

    return refreshed_auth_response, True  # type: ignore


def _set_user_context(auth_response):
    """Set user context in Flask's g object."""
    g.user = auth_response.user
    g.role = auth_response.role
    g.organization_id = auth_response.organization_id


def _create_response_with_cookie(response, sealed_session):
    """Create response with refreshed session cookie."""
    response = make_response(response)
    response.set_cookie(
        "wos_session",
        sealed_session,
        secure=True,
        httponly=True,
        samesite="lax",
        domain=None,
    )
    return response


def socket_auth(*args, **kwargs):
    if not request.cookies.get("wos_session"):
        raise UnauthorizedError("No session cookie")

    session = workos_client.user_management.load_sealed_session(
        sealed_session=request.cookies["wos_session"],
        cookie_password=cookie_password_b64,
    )
    auth_response = session.authenticate()
    if auth_response.authenticated:
        return auth_response

    raise UnauthorizedError("Invalid session")
