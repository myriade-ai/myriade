import json

from flask import Flask, g, jsonify

from auth.auth import SealedSessionAuthResponse, with_auth


def _make_auth_response(session_value: str) -> SealedSessionAuthResponse:
    validation_payload = {
        "user": {"id": "user-1", "email": "user@example.com"},
        "organization_id": "org-1",
        "role": "member",
    }

    return SealedSessionAuthResponse(session_value, validation_payload)


def test_with_auth_sets_cookie_when_session_refreshed_during_request(monkeypatch):
    app = Flask(__name__)
    app.config["TESTING"] = True

    initial_auth_response = _make_auth_response("OLD_SESSION")

    # Patch the authenticate helper used by the decorator so we control the
    # initial response provided to the request wrapper.
    monkeypatch.setattr(
        "auth.auth._authenticate_session",
        lambda cookie: (initial_auth_response, False),
    )

    @app.route("/protected")
    @with_auth
    def protected_route():
        # Simulate the proxy provider refreshing the session during the request
        # lifecycle.
        g.session_refreshed = True
        g.sealed_session = "NEW_SESSION"
        return jsonify({"status": "ok"})

    client = app.test_client()

    client.set_cookie("session", "OLD_SESSION")

    response = client.get("/protected")

    assert response.status_code == 200
    cookies = response.headers.getlist("Set-Cookie")
    assert any("session=NEW_SESSION" in cookie for cookie in cookies)

    data = json.loads(response.data)
    assert data["status"] == "ok"
