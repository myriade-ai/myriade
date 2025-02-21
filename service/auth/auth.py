import base64
import hashlib
import os
from functools import wraps

from flask import g, jsonify, request
from workos import WorkOSClient

workos_client = WorkOSClient(
    api_key=os.environ["WORKOS_API_KEY"],
    client_id=os.environ["WORKOS_CLIENT_ID"],
)

cookie_password = "mkPRI77h3M6iehoYFhwWXQ27f2sGpPuM"

# Generate a proper Fernet key from the password
cookie_password_bytes = cookie_password.encode()
cookie_password_b64 = base64.urlsafe_b64encode(
    hashlib.sha256(cookie_password_bytes).digest()
).decode("utf-8")


def with_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session = workos_client.user_management.load_sealed_session(
            sealed_session=request.cookies.get("wos_session"),
            cookie_password=cookie_password_b64,
        )
        auth_response = session.authenticate()

        if auth_response.authenticated:
            g.user = auth_response.user
            g.role = auth_response.role
            g.organization_id = auth_response.organization_id
            return f(*args, **kwargs)

        if auth_response.authenticated is False:
            return jsonify({"error": "Unauthorized"}), 401

    return decorated_function


def socket_auth(*args, **kwargs):
    session = workos_client.user_management.load_sealed_session(
        sealed_session=request.cookies.get("wos_session"),
        cookie_password=cookie_password_b64,
    )
    auth_response = session.authenticate()
    if auth_response.authenticated:
        return auth_response

    raise Exception("Unauthorized")
