"""Use syrupy to test that the imported functions stay consistent.

We initialize the datachat class and test that the functions are consistent.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from syrupy.assertion import SnapshotAssertion

from back.models import Base, Database, Project, User
from chat.datachat import DatabaseChat


@pytest.fixture
def session():
    """Create a new database session for testing"""
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

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


@pytest.fixture
def user(session):
    """Create a test user"""
    user = User(id="test-user", email="test@test.com")
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def database(session):
    """Create a test database"""
    database = Database(
        name="test",
        _engine="sqlite",
        details={"filename": ":memory:"},
        memory="test memory",
        dbt_manifest={"sources": {}, "nodes": {}},
        dbt_catalog={"sources": {}, "nodes": {}},
    )
    session.add(database)
    session.commit()
    return database


@pytest.fixture
def project(session, database, user):
    """Create a test project"""
    project = Project(
        name="test",
        description="test project",
        tables=[],  # Add dummy tables if needed
        databaseId=database.id,
        creatorId=user.id,
    )
    session.add(project)
    session.commit()
    return project


@pytest.fixture
def datachat(session, database, project):
    """Create a datachat instance with a database and project"""
    return DatabaseChat(
        session=session,
        database_id=database.id,
        project_id=project.id,
        user_id="test-user",
    )


def test_functions(datachat, snapshot: SnapshotAssertion):
    """Test that the functions dictionary stays consistent"""
    chatbot = datachat.chatbot
    # Convert functions to a serializable format
    functions_list = [name for name, _ in chatbot.functions.items()]
    assert functions_list == snapshot


def test_functions_schema(datachat, snapshot: SnapshotAssertion):
    """Test that the functions schema stays consistent"""
    chatbot = datachat.chatbot
    assert chatbot.functions_schema == snapshot


def test_tools(datachat, snapshot: SnapshotAssertion):
    """Test that the tools dictionary stays consistent"""
    chatbot = datachat.chatbot
    # Convert tools to a serializable format
    tools_dict = {
        name: str(tool) if callable(tool) else tool.__class__.__name__
        for name, tool in chatbot.tools.items()
    }
    assert tools_dict == snapshot
