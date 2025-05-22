import requests

from tests.utils import normalise_json


def test_run_simple_query(app_server, test_db_id, snapshot):
    query_payload = {
        "query": "SELECT 1 AS test_col;",
        "databaseId": test_db_id,
    }

    response = requests.post(
        f"{app_server}/query/_run", json=query_payload, cookies={"wos_session": "MOCK"}
    )

    assert response.status_code == 200
    response_data = response.json()

    # Normalize the response before snapshotting
    # The response contains {'rows': [{'test_col': 1}], 'count': 1}
    # Normalization might not be strictly necessary here if results are stable,
    # but it's good practice if any part of the response could be volatile.
    normalized_response = normalise_json(response_data)
    assert normalized_response == snapshot
