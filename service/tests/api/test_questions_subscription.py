import requests


def test_questions_endpoint_structure(app_server, session, test_db_id):
    """Test that questions endpoint is properly set up"""
    # Test with mock authentication and the test database
    response = requests.get(
        f"{app_server}/contexts/database-{test_db_id}/questions",
        cookies={"wos_session": "MOCK"},
    )

    # Should either return questions or subscription error
    # This depends on how the MOCK authentication is set up
    assert response.status_code in [200, 403]

    if response.status_code == 403:
        assert "SUBSCRIPTION_REQUIRED" in response.json().get("message", "")
