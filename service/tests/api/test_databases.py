from unittest.mock import patch

import requests

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
            "dbt_catalog": None,
            "dbt_manifest": None,
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
            "dbt_catalog": None,
            "dbt_manifest": None,
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
