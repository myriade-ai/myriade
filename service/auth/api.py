import logging
from urllib.parse import urlencode

import requests
from flask import Blueprint, g, jsonify, make_response, redirect, request

from auth.auth import _try_refresh_session
from config import ENV, HOST, INFRA_URL
from middleware import user_middleware

logger = logging.getLogger(__name__)

api = Blueprint("auth", __name__)


@api.route("/auth")
def auth():
    # Use auth proxy service
    callback_host = HOST

    try:
        response = requests.get(
            f"{INFRA_URL}/auth",
            params={"callback_host": callback_host},
            timeout=10,
        )
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        error_msg = "Authentication service unavailable"
        if ENV != "production":
            error_msg = f"Auth proxy error: {str(e)}"
        return jsonify({"error": error_msg}), 500


@api.route("/auth/complete")
def auth_complete():
    """
    Complete OAuth flow using intermediate callback pattern.
    Receives temporary token from proxy and exchanges it for auth data.
    """
    temp_token = request.args.get("token")
    if not temp_token:
        error_params = urlencode({"error": "Missing token parameter"})
        return redirect(f"/auth-error?{error_params}")

    try:
        # Exchange temporary token for auth data
        response = requests.post(
            f"{INFRA_URL}/auth/exchange",
            json={"token": temp_token},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        auth_data = response.json()

        # Use sealed session from proxy
        if "sealed_session" not in auth_data:
            raise ValueError("Proxy must provide sealed_session")

        session_cookie = auth_data["sealed_session"]

        response = make_response(redirect("/logged"))
        response.set_cookie(
            "session",
            session_cookie,
            secure=ENV == "production",  # Only over HTTPS in production
            httponly=True,  # Prevent XSS access
            samesite="lax",  # CSRF protection
            max_age=60 * 60 * 24 * 7,  # 7 days
            domain=None,  # Current domain only
            path="/",  # Available to all paths
        )
        return response

    except requests.RequestException as e:
        error_msg = "Failed to exchange token with auth service"
        if ENV != "production":
            error_msg = f"Token exchange failed: {str(e)}"
        error_params = urlencode({"error": error_msg})
        return redirect(f"/auth-error?{error_params}")
    except Exception as e:
        error_msg = "Authentication completion failed"
        if ENV != "production":
            error_msg = str(e)
        error_params = urlencode({"error": error_msg})
        return redirect(f"/auth-error?{error_params}")


@api.route("/user")
@user_middleware
def user():
    return jsonify(
        {
            **g.auth_user.user.__dict__,
            **g.user.to_dict(),
            "role": g.role,
            "organization_id": g.organization_id,
        }
    )


@api.route("/logout", methods=["POST"])
def logout():
    if not request.cookies.get("session"):
        return jsonify({"message": "No session cookie"}), 500

    session_cookie = request.cookies["session"]

    try:
        # For sealed sessions, we need to get session info from the proxy
        headers = {"Authorization": f"Bearer {session_cookie}"}

        # First validate the session to get session info
        validate_response = requests.get(
            f"{INFRA_URL}/auth/validate",
            headers=headers,
            timeout=10,
        )

        if validate_response.status_code != 200:
            # Session is invalid, just clear the cookie
            response = make_response(
                jsonify({"message": "Session invalid, cookie cleared"})
            )
            response.delete_cookie(
                "session",
                path="/",
                domain=None,
                secure=ENV == "production",
                samesite="lax",
            )
            return response

        # For sealed sessions, we'll just clear the local cookie
        # Auth proxy handles session invalidation on their end
        logout_url = f"{HOST}/login"

        response = make_response(
            jsonify({"message": "Logged out successfully", "logout_url": logout_url})
        )
        response.delete_cookie(
            "session", path="/", domain=None, secure=ENV == "production", samesite="lax"
        )
        return response

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # If anything fails, just clear the cookie
        scheme = "https" if ENV == "production" else "http"
        response = make_response(
            jsonify(
                {
                    "message": "Logged out (with errors)",
                    "logout_url": f"{scheme}://{HOST}/",
                }
            )
        )
        response.delete_cookie(
            "session", path="/", domain=None, secure=ENV == "production", samesite="lax"
        )
        return response


# Expose api to debug refresh session
@api.route("/auth/refresh", methods=["GET"])
def refresh():
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return jsonify({"message": "No session cookie"}), 500

    try:
        refreshed_response = _try_refresh_session(session_cookie)
        if refreshed_response:
            # Convert SealedSessionAuthResponse to dictionary for JSON serialization
            response_data = {
                "authenticated": refreshed_response.authenticated,
                "user": {
                    "id": refreshed_response.user.id,
                    "email": refreshed_response.user.email,
                    "first_name": getattr(refreshed_response.user, "first_name", None),
                    "last_name": getattr(refreshed_response.user, "last_name", None),
                },
                "organization_id": refreshed_response.organization_id,
                "access_token": refreshed_response.access_token,
                "refresh_token": refreshed_response.refresh_token,
                "session_id": refreshed_response.session_id,
                "role": refreshed_response.role,
                "sealed_session": refreshed_response.sealed_session,
            }
            return jsonify(
                {
                    "message": "Session refreshed successfully",
                    "refreshed_response": response_data,
                }
            )
        else:
            return jsonify(
                {
                    "message": "Session refresh failed - no refresh token or refresh unsuccessful"  # noqa: E501
                }
            ), 500
    except Exception as e:
        logger.error(f"Session refresh exception: {str(e)}", exc_info=True)
        return jsonify({"message": f"Session refresh failed - {str(e)}"}), 500
