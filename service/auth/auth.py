import hashlib
import logging
import time
from functools import wraps

import requests
from flask import g, jsonify, make_response, request

from config import (
    ENV,
    INFRA_URL,
)

logger = logging.getLogger(__name__)

# Simple in-memory cache for refresh tokens
# Format: {session_cookie_hash: {"refresh_token": token, "expires": timestamp}}
# In production, consider using Redis or a proper cache
_refresh_token_cache = {}

# Session validation cache to avoid calling proxy on every request
# Format: {session_cookie_hash: {"validation_data": data, "expires": timestamp}}
_session_validation_cache = {}


def _cache_refresh_token(session_cookie, refresh_token, ttl_hours=24):
    """Cache a refresh token for a session with TTL"""
    if not refresh_token:
        return

    # Use hash of session cookie as key for security

    cache_key = hashlib.sha256(session_cookie.encode()).hexdigest()[:32]
    expires = time.time() + (ttl_hours * 3600)

    _refresh_token_cache[cache_key] = {
        "refresh_token": refresh_token,
        "expires": expires,
    }

    # Clean up expired entries
    _cleanup_expired_refresh_tokens()


def _get_cached_refresh_token(session_cookie):
    """Get cached refresh token for a session"""
    cache_key = hashlib.sha256(session_cookie.encode()).hexdigest()[:32]

    cached = _refresh_token_cache.get(cache_key)
    if not cached:
        print("not cached")
        return None

    # Check if expired
    if time.time() > cached["expires"]:
        del _refresh_token_cache[cache_key]
        return None

    return cached["refresh_token"]


def _cleanup_expired_refresh_tokens():
    """Remove expired refresh tokens from cache"""
    current_time = time.time()
    expired_keys = [
        key
        for key, data in _refresh_token_cache.items()
        if current_time > data["expires"]
    ]
    for key in expired_keys:
        del _refresh_token_cache[key]


def _cache_session_validation(session_cookie, validation_data, ttl_minutes=10):
    """Cache session validation result to avoid proxy calls on every request"""
    import hashlib

    cache_key = hashlib.sha256(session_cookie.encode()).hexdigest()[:32]
    expires = time.time() + (ttl_minutes * 60)

    _session_validation_cache[cache_key] = {
        "validation_data": validation_data,
        "expires": expires,
    }

    # Clean up expired entries
    _cleanup_expired_validation_cache()


def _get_cached_validation(session_cookie):
    """Get cached validation result if available and not expired"""
    import hashlib

    cache_key = hashlib.sha256(session_cookie.encode()).hexdigest()[:32]
    cached = _session_validation_cache.get(cache_key)

    if not cached:
        return None

    # Check if expired
    if time.time() > cached["expires"]:
        del _session_validation_cache[cache_key]
        return None

    return cached["validation_data"]


def _cleanup_expired_validation_cache():
    """Remove expired validation cache entries"""
    current_time = time.time()
    expired_keys = [
        key
        for key, data in _session_validation_cache.items()
        if current_time > data["expires"]
    ]
    for key in expired_keys:
        del _session_validation_cache[key]


class UnauthorizedError(Exception):
    pass


class SealedSessionAuthResponse:
    def __init__(self, session_cookie, validation_data):
        self.authenticated = True
        self.user = SealedSessionUser(validation_data.get("user", {}))
        self.id = validation_data.get("user", {}).get(
            "id"
        )  # Add id for middleware compatibility
        self.organization_id = validation_data.get("organization_id")
        self.access_token = validation_data.get("access_token") or session_cookie
        self.refresh_token = validation_data.get("refresh_token")
        self.session_id = validation_data.get("session_id")
        self.role = validation_data.get("role", "member")
        self.reason = None
        self.sealed_session = session_cookie  # Keep reference to sealed session


class SealedSessionUser:
    def __init__(self, user_data):
        self.id = user_data.get("id")
        self.email = user_data.get("email")
        self.first_name = user_data.get("first_name")
        self.last_name = user_data.get("last_name")


def with_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validate session cookie exists
        session_cookie = request.cookies.get("session")
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

        # Execute wrapped function
        res = f(*args, **kwargs)

        # Return response with refreshed session cookie if needed
        if is_refreshed:
            return _create_response_with_cookie(res, auth_response.sealed_session)
        return res

    return decorated_function


def _authenticate_session(session_cookie: str):
    """Authenticate session using cached validation to minimize proxy calls."""

    try:
        # First, check if we have a cached validation result
        cached_validation = _get_cached_validation(session_cookie)
        if cached_validation:
            logger.info(
                f"✅ Using cached session validation (no proxy call) for session: {session_cookie[:20]}..."  # noqa: E501
            )
            return SealedSessionAuthResponse(session_cookie, cached_validation), False

        # No cache or expired - validate via proxy
        logger.info("Validating session via proxy (cache miss/expired)")

        headers = {"Authorization": f"Bearer {session_cookie}"}
        response = requests.get(
            f"{INFRA_URL}/auth/validate", headers=headers, timeout=10
        )
        print("_authenticate_session", response.status_code, response.json())

        if response.status_code == 200:
            # Session is valid, extract user data from response
            validation_data = response.json()

            # Cache the validation result to avoid future proxy calls
            logger.info(
                f"💾 Caching validation result for session: {session_cookie[:20]}..."
            )
            _cache_session_validation(session_cookie, validation_data)

            # Cache the refresh token for future use
            refresh_token = validation_data.get("refresh_token")
            print("refresh_token", refresh_token)
            if refresh_token:
                print("caching refresh_token")
                _cache_refresh_token(session_cookie, refresh_token)

            logger.info("Session validated via proxy and cached")
            return SealedSessionAuthResponse(session_cookie, validation_data), False

        elif response.status_code == 401:
            # Session might be expired, attempt to refresh
            logger.info("Proxy validation failed, attempting to refresh...")

            try:
                refreshed_response = _try_refresh_session(session_cookie)
                if refreshed_response:
                    logger.info("Session refreshed successfully")
                    return refreshed_response, True  # Indicate session was refreshed
                else:
                    logger.warning("Session refresh failed")
                    raise UnauthorizedError("Session expired and refresh failed")
            except Exception as refresh_error:
                logger.error(f"Session refresh error: {str(refresh_error)}")
                raise UnauthorizedError("Session expired") from refresh_error

        else:
            logger.warning(
                f"Session validation failed with status {response.status_code}"
            )
            raise UnauthorizedError("Invalid sealed session")

    except requests.RequestException as e:
        logger.error(f"Failed to validate sealed session: {str(e)}")
        raise UnauthorizedError("Session validation failed") from e
    except Exception as e:
        logger.error(f"Session authentication failed: {str(e)}")
        raise UnauthorizedError("Authentication failed: session error") from e


def _try_refresh_session(session_cookie: str):
    """
    Attempt to refresh an expired session by calling the proxy refresh endpoint.

    Returns:
        SealedSessionAuthResponse: New auth response with refreshed session,
                                  or None if refresh failed
    """
    try:
        # Get cached refresh token for this session
        refresh_token = _get_cached_refresh_token(session_cookie)
        if not refresh_token:
            logger.warning("No cached refresh token available for session refresh")
            return None

        # Call proxy refresh endpoint
        logger.info("Attempting to refresh session via proxy")
        refresh_data = {"refresh_token": refresh_token}

        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{INFRA_URL}/auth/refresh", json=refresh_data, headers=headers, timeout=10
        )

        if response.status_code == 200:
            # Refresh successful, get new session data
            refresh_result = response.json()

            # Check if we got a sealed session (preferred) or just refresh data
            new_sealed_session = refresh_result.get("sealed_session")

            if new_sealed_session:
                # We have a sealed session, validate it normally
                headers = {"Authorization": f"Bearer {new_sealed_session}"}
                validate_response = requests.get(
                    f"{INFRA_URL}/auth/validate", headers=headers, timeout=10
                )

                if validate_response.status_code == 200:
                    validation_data = validate_response.json()

                    # Cache the new refresh token
                    new_refresh_token = validation_data.get("refresh_token")
                    if new_refresh_token:
                        _cache_refresh_token(new_sealed_session, new_refresh_token)

                    # Cache the validation result using the NEW session key
                    _cache_session_validation(new_sealed_session, validation_data)

                    logger.info("Session refresh successful via sealed session")
                    return SealedSessionAuthResponse(
                        new_sealed_session, validation_data
                    )
                else:
                    status_code = validate_response.status_code
                    logger.error(f"Failed to validate refreshed session: {status_code}")
                    return None

            elif refresh_result.get("authenticated"):
                # We have refresh data but no sealed session
                # This happens when WorkOS doesn't support sealed
                # session creation from refresh
                logger.info(
                    "Proxy returned refresh data without sealed session - using access token approach"  # noqa: E501
                )

                # Cache the new refresh token for future use
                new_refresh_token = refresh_result.get("refresh_token")
                if new_refresh_token:
                    # Use the access token as a temporary session identifier
                    access_token = refresh_result.get("access_token")
                    if access_token:
                        _cache_refresh_token(access_token, new_refresh_token)

                # Create a temporary "sealed session" using the access token
                # This is not ideal but works as a fallback
                temp_session = refresh_result.get("access_token", session_cookie)

                # Cache the refresh result using the NEW session key (access token)
                _cache_session_validation(temp_session, refresh_result)

                logger.info("Session refresh successful via access token fallback")
                return SealedSessionAuthResponse(temp_session, refresh_result)

            else:
                logger.error("Proxy refresh did not return valid authentication data")
                return None

        else:
            logger.warning(f"Session refresh failed with status {response.status_code}")
            if response.status_code == 400:
                # Refresh token might be expired or invalid, remove from cache
                import hashlib

                cache_key = hashlib.sha256(session_cookie.encode()).hexdigest()[:32]
                _refresh_token_cache.pop(cache_key, None)
            return None

    except requests.RequestException as e:
        logger.error(f"Session refresh request failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Session refresh attempt failed: {str(e)}")
        return None


def _set_user_context(auth_response):
    """Set user context in Flask's g object."""
    g.auth_user = auth_response  # Set the full auth response
    g.role = auth_response.role
    g.organization_id = auth_response.organization_id


def _create_response_with_cookie(response, sealed_session):
    """Create response with refreshed session cookie."""
    response = make_response(response)
    response.set_cookie(
        "session",
        sealed_session,
        secure=ENV == "production",  # Only over HTTPS
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
    """Authenticate socket connections using sealed sessions"""
    if not request.cookies.get("session"):
        raise UnauthorizedError("No session cookie")

    # Use the same authentication logic as the main auth decorator
    auth_response, _ = _authenticate_session(request.cookies["session"])
    if auth_response.authenticated:
        return auth_response

    raise UnauthorizedError("Invalid session")
