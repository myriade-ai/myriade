import logging
from urllib.parse import urlencode

import requests
from flask import Blueprint, g, jsonify, make_response, redirect, request

from auth.infra_utils import make_authenticated_proxy_request
from config import ENV, HOST, INFRA_URL
from middleware import user_middleware

logger = logging.getLogger(__name__)

api = Blueprint("auth", __name__)


@api.route("/auth")
def auth():
    # Use auth proxy service
    callback_host = HOST if HOST else request.url_root.rstrip("/")

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
        logger.error(f"Failed to exchange token with auth service: {str(e)}")
        error_msg = "Failed to exchange token with auth service"
        error_params = urlencode({"error": error_msg})
        return redirect(f"/auth-error?{error_params}")
    except Exception as e:
        logger.error(f"Authentication completion failed: {str(e)}")
        error_msg = "Authentication completion failed"
        error_params = urlencode({"error": error_msg})
        return redirect(f"/auth-error?{error_params}")


@api.route("/auth/logout", methods=["POST"])
def logout():
    if not request.cookies.get("session"):
        return jsonify({"message": "No session cookie"}), 500

    session_cookie = request.cookies["session"]
    callback_host = HOST if HOST else request.url_root.rstrip("/")

    # Clear session from validation and refresh caches
    # This also removes any reverse mappings (old_session → this_session)
    from auth.auth import _invalidate_session_cache

    _invalidate_session_cache(session_cookie)

    try:
        # For WorkOS sealed sessions, get session info from the proxy
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

        # Get session data to extract session_id
        session_data = validate_response.json()
        session_id = session_data.get("session_id")

        if session_id:
            # Properly call proxy logout with session_id
            try:
                logout_response = requests.post(
                    f"{INFRA_URL}/auth/logout",
                    json={
                        "session_id": session_id,
                        "return_to": f"{callback_host}?logged-out=true",
                    },
                    timeout=10,
                )

                if logout_response.status_code == 200:
                    logout_data = logout_response.json()
                    logout_url = logout_data.get(
                        "logout_url", f"{callback_host}?logged-out=true"
                    )
                    logger.info("Successfully called proxy logout")
                else:
                    logger.warning(
                        f"Proxy logout failed with status {logout_response.status_code}"
                    )
                    logout_url = f"{callback_host}?logged-out=true"
            except Exception as proxy_error:
                logger.error(f"Proxy logout request failed: {str(proxy_error)}")
                logout_url = f"{callback_host}?logged-out=true"
        else:
            logger.warning("No session_id found in session data, skipping proxy logout")
            logout_url = f"{callback_host}?logged-out=true"

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
        response = make_response(
            jsonify(
                {"message": "Logged out (with errors)", "logout_url": callback_host}
            )
        )
        response.delete_cookie(
            "session", path="/", domain=None, secure=ENV == "production", samesite="lax"
        )
        return response


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


@api.route("/user/credits")
@user_middleware
def proxy_credits():
    """Proxy credits request to auth service"""
    try:
        response = make_authenticated_proxy_request(
            "/user/credits",
            method="GET",
            timeout=10,
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        logger.error(f"Credits proxy request failed: {str(e)}")
        return jsonify({"error": "Failed to fetch credits from auth service"}), 500
