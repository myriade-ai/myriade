import os
from functools import wraps

from clerk_backend_api import Clerk
from clerk_backend_api.jwks_helpers import AuthenticateRequestOptions
from flask import g, jsonify, request

CLERK_SECRET_KEY = os.environ["CLERK_SECRET_KEY"]
clerk = Clerk(bearer_auth=CLERK_SECRET_KEY)


def clerk_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "No authorization token provided"}), 401

        try:
            # Verify and decode the token
            request_state = clerk.authenticate_request(
                request,
                AuthenticateRequestOptions(),
            )
            g.user_id = request_state.payload["sub"]
        except Exception:
            return jsonify({"error": "Invalid authorization token"}), 401

        user = clerk.users.get(user_id=g.user_id)
        g.user_email = user.email_addresses[0].email_address
        return f(*args, **kwargs)

    return decorated_function
