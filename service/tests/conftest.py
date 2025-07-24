import os
import socket
from threading import Thread

import pytest
import requests
from sqlalchemy.orm import sessionmaker

os.environ["DOTENV_FILE"] = ".env.test"

from app import create_app  # noqa: E402
from back.session import create_engine  # noqa: E402
from config import DATABASE_URL  # noqa: E402
from models import Base, Database  # noqa: E402


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

    server = Thread(
        target=app.run,
        kwargs={
            "host": "localhost",
            "port": port,
            "debug": False,
            "use_reloader": False,
        },
        daemon=True,
    )
    server.start()

    yield f"http://localhost:{port}/api"

    # Teardown (optional, as daemon threads exit with main thread)
    # server.join(timeout=1) # Example of explicit teardown


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
        "dbt_catalog": None,
        "dbt_manifest": None,
    }

    r = requests.post(
        f"{app_server}/databases", json=payload, cookies={"wos_session": "MOCK"}
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
    requests.delete(f"{app_server}/databases/{db_id}", cookies={"wos_session": "MOCK"})
