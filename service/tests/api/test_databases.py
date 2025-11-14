import uuid
from unittest.mock import patch

import requests
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from models import (
    DBT,
    Chart,
    Conversation,
    ConversationMessage,
    Note,
    Project,
    ProjectTables,
    Query,
)
from models.quality import Issue
from tests.utils import normalise_json


def test_create_database(app_server, test_db_id, snapshot):
    r = requests.get(f"{app_server}/databases", cookies={"session": "MOCK"})
    # Check that the database id is in the list
    assert r.status_code == 200
    assert test_db_id in [db["id"] for db in r.json()]


def test_list_databases(app_server, test_db_id, snapshot):
    r = requests.get(f"{app_server}/databases", cookies={"session": "MOCK"})
    assert r.status_code == 200
    assert [normalise_json(db) for db in r.json()] == snapshot


# def test_delete_database(app_server, test_db_id, snapshot):
#     r = requests.delete(
#         f"{app_server}/databases/{test_db_id}", cookies={"session": "MOCK"}
#     )
#     assert r.status_code == 200
#     assert normalise_json(r.json()) == snapshot()


def test_delete_database_with_conversations(app_server, session):
    session.execute(text("PRAGMA foreign_keys=ON"))
    session.commit()

    payload = {
        "name": "cascade-test-db",
        "description": "Database with conversations",
        "engine": "sqlite",
        "details": {"filename": ":memory:"},
        "safe_mode": True,
        "write_mode": "confirmation",
    }

    create_resp = requests.post(
        f"{app_server}/databases", json=payload, cookies={"session": "MOCK"}
    )
    assert create_resp.status_code == 200
    database_id = create_resp.json()["id"]
    database_uuid = uuid.UUID(database_id)

    conversation_resp = requests.post(
        f"{app_server}/conversations",
        json={"contextId": f"database-{database_id}"},
        cookies={"session": "MOCK"},
    )
    assert conversation_resp.status_code == 200
    conversation_id = uuid.UUID(conversation_resp.json()["id"])

    dbt_entry = DBT(database_id=database_uuid)
    session.add(dbt_entry)
    session.flush()

    message = ConversationMessage(
        conversationId=conversation_id,
        role="user",
        content="hello",
    )
    session.add(message)
    session.flush()

    issue = Issue(title="orphaned issue", message_id=message.id)
    session.add(issue)
    session.flush()
    message_id = message.id
    issue_id = issue.id
    session.commit()

    delete_resp = requests.delete(
        f"{app_server}/databases/{database_id}", cookies={"session": "MOCK"}
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"success": True}

    session.expire_all()

    SessionFactory = sessionmaker(bind=session.get_bind())
    verify_session = SessionFactory()
    try:
        assert (
            verify_session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
            is None
        )
        assert (
            verify_session.query(ConversationMessage)
            .filter(ConversationMessage.id == message_id)
            .first()
            is None
        )
        assert (
            verify_session.query(DBT).filter(DBT.database_id == database_uuid).first()
            is None
        )

        refreshed_issue = verify_session.query(Issue).filter(Issue.id == issue_id).one()
        assert refreshed_issue.message_id is None
    finally:
        verify_session.close()


def test_delete_database_with_queries(app_server, session):
    """Test deleting a database with queries and charts (the main foreign key issue)."""
    session.execute(text("PRAGMA foreign_keys=ON"))
    session.commit()

    payload = {
        "name": "query-test-db",
        "description": "Database with queries",
        "engine": "sqlite",
        "details": {"filename": ":memory:"},
        "safe_mode": True,
        "write_mode": "confirmation",
    }

    create_resp = requests.post(
        f"{app_server}/databases", json=payload, cookies={"session": "MOCK"}
    )
    assert create_resp.status_code == 200
    database_id = create_resp.json()["id"]
    database_uuid = uuid.UUID(database_id)

    # Create a query - this is the main foreign key issue being fixed
    query = Query(
        databaseId=database_uuid,
        title="Test Query",
        sql="SELECT 1",
        status="completed",
    )
    session.add(query)
    session.flush()
    query_id = query.id

    # Create a chart linked to the query
    chart = Chart(queryId=query_id, config={"type": "bar"})
    session.add(chart)
    session.flush()
    chart_id = chart.id

    session.commit()

    # Delete the database - this should work now without foreign key violations
    delete_resp = requests.delete(
        f"{app_server}/databases/{database_id}", cookies={"session": "MOCK"}
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"success": True}

    # Verify all related records were deleted
    session.expire_all()

    SessionFactory = sessionmaker(bind=session.get_bind())
    verify_session = SessionFactory()
    try:
        assert verify_session.query(Query).filter(Query.id == query_id).first() is None
        assert verify_session.query(Chart).filter(Chart.id == chart_id).first() is None
    finally:
        verify_session.close()


def test_delete_database_with_projects(app_server, session):
    """Test deleting a database with projects that have conversations (P1 foreign key issue)."""
    session.execute(text("PRAGMA foreign_keys=ON"))
    session.commit()

    payload = {
        "name": "project-test-db",
        "description": "Database with projects",
        "engine": "sqlite",
        "details": {"filename": ":memory:"},
        "safe_mode": True,
        "write_mode": "confirmation",
    }

    create_resp = requests.post(
        f"{app_server}/databases", json=payload, cookies={"session": "MOCK"}
    )
    assert create_resp.status_code == 200
    database_id = create_resp.json()["id"]
    database_uuid = uuid.UUID(database_id)

    # Create a project
    project = Project(
        databaseId=database_uuid,
        name="Test Project",
        description="Test project description",
        creatorId="admin",
    )
    session.add(project)
    session.flush()
    project_id = project.id
    session.commit()  # Commit so the API can see the project

    # Create a conversation linked to the project
    conversation_resp = requests.post(
        f"{app_server}/conversations",
        json={"contextId": f"project-{project_id}"},
        cookies={"session": "MOCK"},
    )
    assert conversation_resp.status_code == 200
    conversation_id = uuid.UUID(conversation_resp.json()["id"])

    # Delete the database - should handle project/conversation foreign key correctly
    delete_resp = requests.delete(
        f"{app_server}/databases/{database_id}", cookies={"session": "MOCK"}
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"success": True}

    # Verify all related records were deleted or updated
    session.expire_all()

    SessionFactory = sessionmaker(bind=session.get_bind())
    verify_session = SessionFactory()
    try:
        # Project should be deleted
        assert (
            verify_session.query(Project).filter(Project.id == project_id).first()
            is None
        )
        # Conversation should still exist but with projectId set to NULL
        conversation = (
            verify_session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        # Conversation is deleted with the database since it references databaseId
        assert conversation is None
    finally:
        verify_session.close()


def test_delete_database_with_project_tables_and_notes(app_server, session):
    """Test deleting a database with projects that have saved tables and notes."""
    session.execute(text("PRAGMA foreign_keys=ON"))
    session.commit()

    payload = {
        "name": "project-tables-test-db",
        "description": "Database with project tables",
        "engine": "sqlite",
        "details": {"filename": ":memory:"},
        "safe_mode": True,
        "write_mode": "confirmation",
    }

    create_resp = requests.post(
        f"{app_server}/databases", json=payload, cookies={"session": "MOCK"}
    )
    assert create_resp.status_code == 200
    database_id = create_resp.json()["id"]
    database_uuid = uuid.UUID(database_id)

    # Create a project
    project = Project(
        databaseId=database_uuid,
        name="Test Project with Tables",
        description="Test project with saved tables",
        creatorId="admin",
    )
    session.add(project)
    session.flush()
    project_id = project.id

    # Create project tables
    project_table = ProjectTables(
        projectId=project_id,
        databaseName="test_db",
        schemaName="public",
        tableName="test_table",
    )
    session.add(project_table)
    session.flush()
    project_table_id = project_table.id

    # Create a note for the project
    note = Note(projectId=project_id, title="Test Note", content="This is a test note")
    session.add(note)
    session.flush()
    note_id = note.id
    session.commit()

    # Delete the database - should handle project_tables/notes foreign keys correctly
    delete_resp = requests.delete(
        f"{app_server}/databases/{database_id}", cookies={"session": "MOCK"}
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json() == {"success": True}

    # Verify all related records were deleted
    session.expire_all()

    SessionFactory = sessionmaker(bind=session.get_bind())
    verify_session = SessionFactory()
    try:
        # Project should be deleted
        assert (
            verify_session.query(Project).filter(Project.id == project_id).first()
            is None
        )
        # Project table should be deleted
        assert (
            verify_session.query(ProjectTables)
            .filter(ProjectTables.id == project_table_id)
            .first()
            is None
        )
        # Note should be deleted
        assert verify_session.query(Note).filter(Note.id == note_id).first() is None
    finally:
        verify_session.close()


def test_authorization_null_organization_vulnerability(app_server, session):
    """
    Test that users without an organization (organization_id=NULL) cannot access
    databases owned by other users without an organization.

    This tests the fix for DEV-433: When both database.organisationId and
    g.organization_id are NULL, access should be denied unless the user is the owner.
    """

    # Mock User A with no organization
    class MockUserA:
        def __init__(self):
            self.id = "user_a"
            self.email = "user_a@example.com"
            self.first_name = "User"
            self.last_name = "A"
            self.role = "user"

    class MockAuthUserA:
        def __init__(self):
            self.authenticated = True
            self.user = MockUserA()
            self.id = "user_a"
            self.organization_id = None  # No organization
            self.access_token = "MOCK_A"
            self.refresh_token = "mock_refresh_token_a"
            self.session_id = "mock_session_id_a"
            self.role = "user"
            self.reason = None
            self.sealed_session = "MOCK_A"

    # Mock User B with no organization
    class MockUserB:
        def __init__(self):
            self.id = "user_b"
            self.email = "user_b@example.com"
            self.first_name = "User"
            self.last_name = "B"
            self.role = "user"

    class MockAuthUserB:
        def __init__(self):
            self.authenticated = True
            self.user = MockUserB()
            self.id = "user_b"
            self.organization_id = None  # No organization
            self.access_token = "MOCK_B"
            self.refresh_token = "mock_refresh_token_b"
            self.session_id = "mock_session_id_b"
            self.role = "user"
            self.reason = None
            self.sealed_session = "MOCK_B"

    # User A creates a database (with no organization)
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserA(), False)

        payload = {
            "name": "user-a-private-db",
            "description": "User A's private database",
            "engine": "sqlite",
            "details": {"filename": ":memory:"},
            "safe_mode": True,
            "write_mode": "confirmation",
        }

        r = requests.post(
            f"{app_server}/databases", json=payload, cookies={"session": "MOCK_A"}
        )
        assert r.status_code == 200
        db_id = r.json()["id"]

    # User B (also without organization) tries to access the database
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserB(), False)

        # Try to get the database schema (read operation)
        r = requests.get(
            f"{app_server}/databases/{db_id}/schema", cookies={"session": "MOCK_B"}
        )
        assert r.status_code == 403, (
            "User B should not be able to access User A's database"
        )
        assert r.json()["error"] == "Access denied"

        # Try to update the database (write operation)
        r = requests.put(
            f"{app_server}/databases/{db_id}",
            json={
                "name": "hacked",
                "description": "hacked",
                "engine": "sqlite",
                "details": {"filename": ":memory:"},
                "write_mode": "confirmation",
            },
            cookies={"session": "MOCK_B"},
        )
        assert r.status_code == 403, (
            "User B should not be able to update User A's database"
        )
        assert r.json()["error"] == "Access denied"

        # Try to sync metadata (write operation that was vulnerable)
        r = requests.post(
            f"{app_server}/databases/{db_id}/sync-metadata",
            cookies={"session": "MOCK_B"},
        )
        assert r.status_code == 403, (
            "User B should not be able to sync metadata for User A's database"
        )

    # User A should still be able to access their own database
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserA(), False)

        r = requests.get(
            f"{app_server}/databases/{db_id}/schema", cookies={"session": "MOCK_A"}
        )
        assert r.status_code == 200, (
            "User A should be able to access their own database"
        )

    # Clean up
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserA(), False)
        requests.delete(
            f"{app_server}/databases/{db_id}", cookies={"session": "MOCK_A"}
        )


def test_share_database_to_organisation(app_server):
    """
    Test that database owners can share databases with their organisation,
    and other organisation members can then access the shared database.
    """

    # Mock User A with an organization
    class MockUserA:
        def __init__(self):
            self.id = "user_a"
            self.email = "user_a@example.com"
            self.first_name = "User"
            self.last_name = "A"
            self.role = "admin"

    class MockAuthUserA:
        def __init__(self):
            self.authenticated = True
            self.user = MockUserA()
            self.id = "user_a"
            self.organization_id = "org_1"
            self.access_token = "MOCK_A"
            self.refresh_token = "mock_refresh_token_a"
            self.session_id = "mock_session_id_a"
            self.role = "admin"
            self.reason = None
            self.sealed_session = "MOCK_A"

    # Mock User B in the same organization
    class MockUserB:
        def __init__(self):
            self.id = "user_b"
            self.email = "user_b@example.com"
            self.first_name = "User"
            self.last_name = "B"
            self.role = "user"

    class MockAuthUserB:
        def __init__(self):
            self.authenticated = True
            self.user = MockUserB()
            self.id = "user_b"
            self.organization_id = "org_1"  # Same organization
            self.access_token = "MOCK_B"
            self.refresh_token = "mock_refresh_token_b"
            self.session_id = "mock_session_id_b"
            self.role = "user"
            self.reason = None
            self.sealed_session = "MOCK_B"

    # User A creates a database (initially private)
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserA(), False)

        payload = {
            "name": "user-a-database",
            "description": "User A's database",
            "engine": "sqlite",
            "details": {"filename": ":memory:"},
            "safe_mode": True,
            "write_mode": "confirmation",
        }

        r = requests.post(
            f"{app_server}/databases", json=payload, cookies={"session": "MOCK_A"}
        )
        assert r.status_code == 200
        db_id = r.json()["id"]
        # Should be shared with org by default since user has org
        assert r.json()["organisationId"] == "org_1"

    # User B should be able to access it since it's shared with org
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserB(), False)

        r = requests.get(
            f"{app_server}/databases/{db_id}/schema", cookies={"session": "MOCK_B"}
        )
        assert r.status_code == 200

    # User A unshares the database from the organisation
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserA(), False)

        r = requests.put(
            f"{app_server}/databases/{db_id}/share",
            json={"share_to_organisation": False},
            cookies={"session": "MOCK_A"},
        )
        assert r.status_code == 200
        assert r.json()["organisationId"] is None

    # User B should no longer be able to access it
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserB(), False)

        r = requests.get(
            f"{app_server}/databases/{db_id}/schema", cookies={"session": "MOCK_B"}
        )
        assert r.status_code == 403
        assert r.json()["error"] == "Access denied"

    # User A shares it again
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserA(), False)

        r = requests.put(
            f"{app_server}/databases/{db_id}/share",
            json={"share_to_organisation": True},
            cookies={"session": "MOCK_A"},
        )
        assert r.status_code == 200
        assert r.json()["organisationId"] == "org_1"

    # User B should now be able to access it again
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserB(), False)

        r = requests.get(
            f"{app_server}/databases/{db_id}/schema", cookies={"session": "MOCK_B"}
        )
        assert r.status_code == 200

    # User B should NOT be able to share/unshare (only owner can)
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserB(), False)

        r = requests.put(
            f"{app_server}/databases/{db_id}/share",
            json={"share_to_organisation": False},
            cookies={"session": "MOCK_B"},
        )
        assert r.status_code == 403
        assert r.json()["error"] == "Only the database owner can share it"

    # Clean up
    with patch("auth.auth._authenticate_session") as mock_auth:
        mock_auth.return_value = (MockAuthUserA(), False)
        requests.delete(
            f"{app_server}/databases/{db_id}", cookies={"session": "MOCK_A"}
        )
