import base64
import hashlib
import logging
from functools import lru_cache, wraps
from threading import RLock

from flask import g, jsonify, make_response, request
from workos.types.user_management.session import (
    AuthenticateWithSessionCookieSuccessResponse,
)

from config import (
    COOKIE_PASSWORD,
    OFFLINE_MODE,
    WORKOS_CLIENT_ID,
    WORKOS_ORGANIZATION_ID,
)

if OFFLINE_MODE:
    from auth.mock import MockWorkOSClient as WorkOSClient
else:
    from workos import WorkOSClient

logger = logging.getLogger(__name__)

workos_client = WorkOSClient(
    client_id=WORKOS_CLIENT_ID,
)
_refresh_locks = lru_cache(maxsize=1024)(lambda sid: RLock())

# Generate a proper Fernet key from the password
cookie_password_bytes = COOKIE_PASSWORD.encode()
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
            logger.warning("No session cookie found")
            return jsonify({"error": "No session cookie"}), 401

        logger.info(f"Authenticating session: {session_cookie[:20]}...")

        # Load and authenticate session
        try:
            auth_response, is_refreshed = _authenticate_session(session_cookie)
            logger.info(f"Authentication successful, refreshed: {is_refreshed}")
        except UnauthorizedError as e:
            logger.error(f"Authentication failed: {str(e)}")
            return jsonify({"error": str(e)}), 401

        # Set user context
        _set_user_context(auth_response)

        # Check if user is in the organization if WORKOS_ORGANIZATION_ID is set
        if (
            WORKOS_ORGANIZATION_ID
            and auth_response.organization_id != WORKOS_ORGANIZATION_ID
        ):
            print(
                "ERROR: User is not in the organization",
                auth_response.organization_id,
                WORKOS_ORGANIZATION_ID,
            )
            return jsonify({"error": "User is not in the organization"}), 401

        # Execute wrapped function
        res = f(*args, **kwargs)

        # Return response with refreshed session cookie if needed
        if is_refreshed:
            return _create_response_with_cookie(res, auth_response.sealed_session)
        return res

    return decorated_function


def _authenticate_session(
    session_cookie: str,
) -> tuple[AuthenticateWithSessionCookieSuccessResponse, bool]:
    """Authenticate and potentially refresh the session."""
    session = workos_client.user_management.load_sealed_session(
        sealed_session=session_cookie,
        cookie_password=cookie_password_b64,
    )

    # ensure only one concurrent refresh per session
    with _refresh_locks(session.client_id):
        auth_response = session.authenticate()
        if auth_response.authenticated:
            return auth_response, False  # type: ignore

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
        secure=True,  # Only over HTTPS
        httponly=True,  # Not accessible via JavaScript
        samesite="lax",  # CSRF protection
        domain=None,  # Current domain only
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",  # Available to all paths
    )
    # Add header to ensure cookie is set
    response.headers["X-Session-Refreshed"] = "true"

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
