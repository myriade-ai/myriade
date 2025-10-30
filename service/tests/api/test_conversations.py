import requests

from tests.utils import normalise_json


def test_create_conversation(app_server, test_db_id, snapshot):
    response = requests.post(
        f"{app_server}/conversations",
        json={"contextId": f"database-{test_db_id}"},
        cookies={"session": "MOCK"},
    )
    assert response.status_code == 200
    assert normalise_json(response.json()) == snapshot
