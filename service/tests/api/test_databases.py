import requests

from tests.utils import normalise_json


def test_create_database(app_server, test_db_id, snapshot):
    r = requests.get(f"{app_server}/databases", cookies={"wos_session": "MOCK"})
    # Check that the database id is in the list
    assert r.status_code == 200
    assert test_db_id in [db["id"] for db in r.json()]


def test_list_databases(app_server, test_db_id, snapshot):
    r = requests.get(f"{app_server}/databases", cookies={"wos_session": "MOCK"})
    assert r.status_code == 200
    assert [normalise_json(db) for db in r.json()] == snapshot


# def test_delete_database(app_server, test_db_id, snapshot):
#     r = requests.delete(
#         f"{app_server}/databases/{test_db_id}", cookies={"wos_session": "MOCK"}
#     )
#     assert r.status_code == 200
#     assert normalise_json(r.json()) == snapshot()
