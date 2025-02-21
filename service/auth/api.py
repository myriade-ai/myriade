from urllib.parse import urlencode

from flask import Blueprint, g, jsonify, make_response, redirect, request

from auth.auth import cookie_password_b64, with_auth, workos_client

api = Blueprint("auth", __name__)


@api.route("/auth")
def auth():
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    print("auth scheme", scheme)
    redirect_uri = scheme + "://" + request.host + "/auth/callback"
    authorization_url = workos_client.sso.get_authorization_url(
        provider="authkit",
        redirect_uri=redirect_uri,
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

        response = make_response(redirect("/"))
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
    response = make_response(jsonify({"message": "Logged out successfully"}))
    response.delete_cookie(
        "wos_session", path="/", domain=None, secure=True, samesite="lax"
    )
    return response
