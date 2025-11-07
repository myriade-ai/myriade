import os
import socket
from threading import Thread
from unittest.mock import patch

# Add eventlet monkey patching BEFORE any other imports that might use threading
import eventlet
import pytest
import requests
from sqlalchemy.orm import sessionmaker

eventlet.monkey_patch()

os.environ["DOTENV_FILE"] = ".env.test"

# Now import your app modules after monkey patching
from app import create_app, socketio  # noqa: E402
from back.session import create_engine  # noqa: E402
from config import DATABASE_URL  # noqa: E402
from models import Base, Database  # noqa: E402


class MockAuthResponse:
    def __init__(self):
        self.authenticated = True
        self.user = MockUser()
        self.id = "admin"  # Add id property for middleware compatibility
        self.organization_id = "mock"
        self.access_token = "MOCK"
        self.refresh_token = "mock_refresh_token"
        self.session_id = "mock_session_id"
        self.role = "admin"
        self.reason = None
        self.sealed_session = "MOCK"


class MockUser:
    def __init__(self):
        self.id = "admin"
        self.email = "test@example.com"
        self.first_name = "Test"
        self.last_name = "User"
        self.role = "admin"


@pytest.fixture(scope="session", autouse=True)
def mock_auth():
    """Mock authentication functions for all tests"""
    mock_org_data = {
        "id": "mock",
        "name": "Test Organization",
        "slug": "test-org",
        "status": "active",
        "plan": "enterprise",
        "features": ["advanced_analytics", "api_access"],
        "limits": {"max_databases": 100, "max_queries_per_month": 10000},
    }

    with (
        patch("auth.auth._authenticate_session") as mock_auth_session,
        patch("auth.infra_utils.get_organization_data") as mock_org,
        patch("back.background_sync.run_metadata_sync_background") as mock_bg_sync,
    ):
        # Mock the session authentication to return our mock response
        mock_auth_session.return_value = (MockAuthResponse(), False)

        # Mock organization data
        mock_org.return_value = mock_org_data

        # Mock background sync to prevent async operations during tests
        mock_bg_sync.return_value = None

        yield


@pytest.fixture(scope="session")
def session():
    """Create a new database session for testing"""
    # Create a test database
    engine = create_engine(DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create a sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create a new session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def app_server(session):
    app = create_app()

    # Find a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()

    def run_server():
        socketio.run(
            app,
            host="localhost",
            port=port,
            debug=False,
            use_reloader=False,
            log_output=False,  # Reduce noise in tests
        )

    server = Thread(target=run_server, daemon=True)
    server.start()

    # Give the server a moment to start
    import time

    time.sleep(0.5)

    yield f"http://localhost:{port}/api"


@pytest.fixture(scope="session")
def test_db_id(app_server, session):
    """
    Spin-up a SQLite DB for the whole test session and
    return its id.  Deleted automatically at the end.
    """
    payload = {
        "name": "pytest-sqlite",
        "description": "ephemeral test db",
        "engine": "sqlite",
        "details": {"filename": ":memory:"},
        "safe_mode": True,
        "write_mode": "confirmation",
    }

    r = requests.post(
        f"{app_server}/databases", json=payload, cookies={"session": "MOCK"}
    )
    r.raise_for_status()

    # change the id to a stable id for the test db
    import uuid

    db_id = uuid.UUID(r.json()["id"])
    fixed_db_id = uuid.UUID("a0000000-0000-0000-0000-000000000001")
    session.query(Database).filter(Database.id == db_id).update({"id": fixed_db_id})
    session.commit()
    yield str(fixed_db_id)  # give the id to tests

    # teardown – remove the DB
    requests.delete(f"{app_server}/databases/{db_id}", cookies={"session": "MOCK"})
