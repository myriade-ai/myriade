"""Tests for WorkspaceTool functionality."""

import json
import uuid

import pytest

from chat.tools.workspace import WorkspaceTool
from models import Conversation, ConversationMessage, Database, Project, Query, User


@pytest.fixture
def user(session):
    """Create a test user"""
    # Generate a unique ID to avoid conflicts
    user_id = f"test-user-{uuid.uuid4()}"
    user = User(id=user_id, email=f"{user_id}@test.com")
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def database(session):
    """Create a test database"""
    database = Database(
        name=f"test-{uuid.uuid4()}",
        engine="sqlite",
        details={"filename": ":memory:"},
        memory="test memory",
    )
    session.add(database)
    session.commit()
    return database


@pytest.fixture
def project(session, database, user):
    """Create a test project"""
    project = Project(
        name=f"test-{uuid.uuid4()}",
        description="test project",
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
def workspace_tool(session, conversation):
    """Create a workspace tool instance"""
    return WorkspaceTool(session=session, conversation_id=conversation.id)


@pytest.fixture
def test_query(session, database, conversation):
    """Create a test query with results"""
    query = Query(
        title="Test Query",
        databaseId=database.id,
        sql="SELECT 1 as id, 'test' as name",
        rows=[{"id": 1, "name": "test"}],
        count=1,
        columns=[{"name": "id", "type": "INTEGER"}, {"name": "name", "type": "TEXT"}],
        status="completed",
    )
    session.add(query)
    session.flush()

    # Link query to conversation via a message
    message = ConversationMessage(
        conversationId=conversation.id,
        role="function",
        content="Query executed",
        queryId=query.id,
    )
    session.add(message)
    session.commit()

    return query


@pytest.fixture
def test_query_no_results(session, database, conversation):
    """Create a test query without results"""
    query = Query(
        title="Query Without Results",
        databaseId=database.id,
        sql="SELECT * FROM users LIMIT 10",
        status="pending_confirmation",
    )
    session.add(query)
    session.flush()

    # Link query to conversation via a message
    message = ConversationMessage(
        conversationId=conversation.id,
        role="function",
        content="Query created",
        queryId=query.id,
    )
    session.add(message)
    session.commit()

    return query


def test_get_query_success(workspace_tool, test_query):
    """Test getting query details by ID"""
    result = workspace_tool.get_query(str(test_query.id))

    # Parse the JSON result
    result_data = json.loads(result)

    assert result_data["id"] == str(test_query.id)
    assert result_data["title"] == "Test Query"
    assert result_data["sql"] == "SELECT 1 as id, 'test' as name"
    assert result_data["status"] == "completed"
    assert result_data["row_count"] == 1
    assert len(result_data["columns"]) == 2
    assert len(result_data["sample_rows"]) == 1
    assert result_data["sample_rows"][0] == {"id": 1, "name": "test"}


def test_get_query_no_results(workspace_tool, test_query_no_results):
    """Test getting query details for query without results"""
    result = workspace_tool.get_query(str(test_query_no_results.id))

    # Parse the JSON result
    result_data = json.loads(result)

    assert result_data["id"] == str(test_query_no_results.id)
    assert result_data["title"] == "Query Without Results"
    assert result_data["sql"] == "SELECT * FROM users LIMIT 10"
    assert result_data["status"] == "pending_confirmation"
    # No results should be present
    assert "row_count" not in result_data
    assert "columns" not in result_data
    assert "sample_rows" not in result_data


def test_get_query_invalid_id(workspace_tool):
    """Test getting query with invalid UUID format"""
    result = workspace_tool.get_query("not-a-valid-uuid")
    assert "Invalid query ID format" in result


def test_get_query_not_found(workspace_tool):
    """Test getting query that doesn't exist"""
    random_uuid = str(uuid.uuid4())
    result = workspace_tool.get_query(random_uuid)
    assert "not found in this conversation" in result


def test_get_query_wrong_conversation(session, database, workspace_tool):
    """Test getting query from a different conversation"""
    # Create a query in a different conversation
    from models import Conversation

    other_conversation = Conversation(databaseId=database.id)
    session.add(other_conversation)
    session.flush()

    other_query = Query(
        title="Other Query",
        databaseId=database.id,
        sql="SELECT 2",
        status="completed",
    )
    session.add(other_query)
    session.flush()

    # Link to different conversation
    message = ConversationMessage(
        conversationId=other_conversation.id,
        role="function",
        content="Query executed",
        queryId=other_query.id,
    )
    session.add(message)
    session.commit()

    # Try to get it from workspace_tool (which is for a different conversation)
    result = workspace_tool.get_query(str(other_query.id))
    assert "not found in this conversation" in result


def test_run_query_by_id_success(workspace_tool, test_query):
    """Test running a query by ID"""
    result = workspace_tool.run_query_by_id(str(test_query.id))

    # Should contain results
    assert "Results" in result
    assert "1/1 rows" in result or "rows:" in result


def test_run_query_by_id_invalid_id(workspace_tool):
    """Test running query with invalid UUID format"""
    result = workspace_tool.run_query_by_id("not-a-valid-uuid")
    assert "Invalid query ID format" in result


def test_run_query_by_id_not_found(workspace_tool):
    """Test running query that doesn't exist"""
    random_uuid = str(uuid.uuid4())
    result = workspace_tool.run_query_by_id(random_uuid)
    assert "not found in this conversation" in result


def test_run_query_by_id_no_sql(session, database, conversation):
    """Test running query that has no SQL"""
    workspace_tool = WorkspaceTool(session=session, conversation_id=conversation.id)

    query = Query(
        title="Empty Query",
        databaseId=database.id,
        sql=None,
        status="completed",
    )
    session.add(query)
    session.flush()

    # Link to conversation
    message = ConversationMessage(
        conversationId=conversation.id,
        role="function",
        content="Query created",
        queryId=query.id,
    )
    session.add(message)
    session.commit()

    result = workspace_tool.run_query_by_id(str(query.id))
    assert "has no SQL to execute" in result


def test_workspace_tool_repr(workspace_tool, test_query):
    """Test the __repr__ method lists queries"""
    result = str(workspace_tool)

    assert "Queries:" in result
    assert str(test_query.id) in result
    assert "Test Query" in result
    assert "Charts:" in result
