from urllib.parse import urlencode

from flask import Blueprint, g, jsonify, make_response, redirect, request

from auth.auth import cookie_password_b64, with_auth, workos_client
from config import WORKOS_ORGANIZATION_ID

api = Blueprint("auth", __name__)


@api.route("/auth")
def auth():
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    redirect_uri = scheme + "://" + request.host + "/auth/callback"
    authorization_url = workos_client.sso.get_authorization_url(
        provider="authkit",
        redirect_uri=redirect_uri,
        organization_id=WORKOS_ORGANIZATION_ID,
    )
    return jsonify({"authorization_url": authorization_url})


@api.route("/callback")
def callback():
    if request.args.get("error"):
        error_params = urlencode(
            {
                "error": request.args.get("error"),
                "error_description": request.args.get("error_description"),
                "error_uri": request.args.get("error_uri"),
            }
        )
        return redirect(f"/auth-error?{error_params}")

    code = request.args.get("code")

    try:
        auth_response = workos_client.user_management.authenticate_with_code(
            code=code,
            session={"seal_session": True, "cookie_password": cookie_password_b64},
        )

        response = make_response(redirect("/logged"))
        response.set_cookie(
            "wos_session",
            auth_response.sealed_session,
            secure=True,
            httponly=True,
            samesite="lax",
            domain=None,  # This will be set automatically based on the domain
        )
        return response

    except Exception as e:
        error_params = urlencode({"error": str(e)})
        return redirect(f"/auth-error?{error_params}")


@api.route("/user")
@with_auth
def user():
    return jsonify(
        {**g.user.__dict__, "role": g.role, "organization_id": g.organization_id}
    )


@api.route("/logout", methods=["POST"])
def logout():
    if not request.cookies.get("wos_session"):
        return jsonify({"message": "No session cookie"}), 500

    session_cookie = request.cookies["wos_session"]
    session = workos_client.user_management.load_sealed_session(
        sealed_session=session_cookie,
        cookie_password=cookie_password_b64,
    )
    auth_result = session.authenticate()
    if not auth_result.authenticated:
        print("ERROR: Failed to authenticate session", auth_result.reason)
        return jsonify({"message": "Failed to authenticate session"}), 500

    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    redirect_url = scheme + "://" + request.host + "/login"

    logout_url = workos_client.user_management.get_logout_url(
        session_id=auth_result.session_id,
        return_to=redirect_url,
    )
    response = make_response(
        jsonify({"message": "Logged out successfully", "logout_url": logout_url})
    )
    response.delete_cookie(
        "wos_session", path="/", domain=None, secure=True, samesite="lax"
    )
    return response
