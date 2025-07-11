import requests

from tests.utils import normalise_json


def test_create_conversation(app_server, snapshot):
    response = requests.post(
        f"{app_server}/conversations",
        json={"contextId": "database-00000000-0000-0000-0000-000000000000"},
        cookies={"wos_session": "MOCK"},
    )
    assert response.status_code == 200
    assert normalise_json(response.json()) == snapshot
