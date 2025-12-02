import requests

from tests.utils import normalise_json

created_query_id_for_favorite_test = None


def test_create_query_for_favorite_testing(app_server, test_db_id, snapshot):
    """Create a query to be used in favorite tests."""
    global created_query_id_for_favorite_test
    query_payload = {
        "title": "Test Query for Favorites",
        "sql": "SELECT 100 AS fav_col;",
        "databaseId": test_db_id,
    }
    response = requests.post(
        f"{app_server}/query",  # Endpoint to create a persistent query object
        json=query_payload,
        cookies={"session": "MOCK"},
    )
    assert response.status_code == 200
    response_data = response.json()
    created_query_id_for_favorite_test = response_data.get("id")
    assert created_query_id_for_favorite_test is not None, (
        "Query ID should not be None after creation"
    )

    # Snapshot the created query (optional, but good for consistency)
    assert normalise_json(response_data) == snapshot


def test_toggle_query_favorite_and_list(app_server, test_db_id, snapshot):
    """Test toggling a query's favorite status and listing favorites.

    Note: The /favorites endpoint only returns queries with rows (executed queries).
    Since the test query is not executed, it won't appear in the favorites list,
    but we can still test the favorite/unfavorite toggle functionality.
    """
    global created_query_id_for_favorite_test
    assert created_query_id_for_favorite_test is not None, (
        "Query ID for favorite test not set."
    )

    # 1. Favorite the query
    response_fav = requests.post(
        f"{app_server}/query/{created_query_id_for_favorite_test}/favorite",
        cookies={"session": "MOCK"},
    )
    assert response_fav.status_code == 200
    assert normalise_json(response_fav.json()) == snapshot(name="favorite_response")
    assert response_fav.json().get("is_favorite") is True

    # 2. List favorites - query won't appear because it has no rows (not executed)
    # The /favorites endpoint filters by Query.rows.isnot(None)
    response_list_fav = requests.get(
        f"{app_server}/favorites?contextId=database-{test_db_id}",
        cookies={"session": "MOCK"},
    )
    assert response_list_fav.status_code == 200
    favorites_data = normalise_json(response_list_fav.json())
    assert favorites_data == snapshot(name="list_favorites_after_favoriting")

    # # Check that our specific query is in the favorites list
    assert any(
        q.get("id") == created_query_id_for_favorite_test
        for q in response_list_fav.json().get("queries", [])
    )

    # 3. Unfavorite the query
    response_unfav = requests.post(
        # Calling again toggles it off
        f"{app_server}/query/{created_query_id_for_favorite_test}/favorite",
        cookies={"session": "MOCK"},
    )
    assert response_unfav.status_code == 200
    assert normalise_json(response_unfav.json()) == snapshot(name="unfavorite_response")
    assert response_unfav.json().get("is_favorite") is False

    # 4. List favorites again
    response_list_unfav = requests.get(
        f"{app_server}/favorites?contextId=database-{test_db_id}",
        cookies={"session": "MOCK"},
    )
    assert response_list_unfav.status_code == 200
    favorites_data_after_unfav = normalise_json(response_list_unfav.json())
    assert favorites_data_after_unfav == snapshot(
        name="list_favorites_after_unfavoriting"
    )

    # # Check that our specific query is NOT in the favorites list
    assert not any(
        q.get("id") == created_query_id_for_favorite_test
        for q in response_list_unfav.json().get("queries", [])
    )
