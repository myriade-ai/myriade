import auth.auth as auth_module
import telemetry
from app import create_app
from tests.conftest import MockAuthResponse


def test_denies_user_outside_allowed_org(monkeypatch, session):
    monkeypatch.setattr(telemetry, "MYRIADE_TELEMETRY_DISABLED", True)
    monkeypatch.setattr(
        auth_module,
        "_authenticate_session",
        lambda session_cookie: (MockAuthResponse(), False),
    )
    monkeypatch.setattr(auth_module, "ALLOWED_ORGANIZATION_ID", "org_123")
    app = create_app()
    client = app.test_client()
    client.set_cookie("session", "MOCK")

    response = client.get("/api/user")

    assert response.status_code == 451
    assert response.json["error"] == "Organization restricted"


def test_allows_user_in_allowed_org(monkeypatch, session):
    monkeypatch.setattr(telemetry, "MYRIADE_TELEMETRY_DISABLED", True)
    monkeypatch.setattr(
        auth_module,
        "_authenticate_session",
        lambda session_cookie: (MockAuthResponse(), False),
    )
    monkeypatch.setattr(auth_module, "ALLOWED_ORGANIZATION_ID", "mock")
    app = create_app()
    client = app.test_client()
    client.set_cookie("session", "MOCK")

    response = client.get("/api/user")

    assert response.status_code == 200
    assert response.json["organization_id"] == "mock"
