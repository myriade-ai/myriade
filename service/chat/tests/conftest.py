"""Shared fixtures for chat service tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chat.analyst_agent import DataAnalystAgent
from models import Base, Conversation, Database, Project, User


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
        engine="sqlite",
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
def conversation(session, user, database, project):
    """Create a test conversation"""
    conv = Conversation(ownerId=user.id, databaseId=database.id, projectId=project.id)
    session.add(conv)
    session.commit()
    return conv


@pytest.fixture
def analyst_agent(session, conversation):
    """Create a data analyst agent instance with a database and project"""
    return DataAnalystAgent(
        session=session,
        conversation=conversation,
    )


@pytest.fixture
def analyst_agent_dbt(session, conversation):
    """Create a data analyst agent instance with a database and project"""
    agent = DataAnalystAgent(
        session=session,
        conversation=conversation,
    )
    agent.conversation.database.dbt_repo_path = "test"
    agent.conversation.database.dbt_catalog = {"sources": {}, "nodes": {}}
    agent.conversation.database.dbt_manifest = {"sources": {}, "nodes": {}}
    return agent
