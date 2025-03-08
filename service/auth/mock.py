"""Useful for offline development"""

from flask import g

# Mock user data for development mode
MOCK_USER_DATA = {
    "id": "admin",
    "email": "admin@localhost",
    "first_name": "Local",
    "last_name": "Dev",
    "organization_id": "mock",
    "role": "admin",
}

# Mock organization data for development mode
MOCK_ORGANIZATION_DATA = {
    "id": "mock",
    "name": "Local Development Organization",
    "domains": ["localhost"],
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z",
}


# Add MockSSOClient class
class MockSSOClient:
    def get_authorization_url(self, provider, redirect_uri):
        return "http://localhost:4000/callback?code=mock_code"


# Mock WorkOS client for development mode
class MockWorkOSClient:
    def __init__(self, api_key, client_id):
        self.organizations = MockOrganizationsClient()
        self.user_management = MockUserManagementClient()
        self.sso = MockSSOClient()


# Mock Organizations client for development mode
class MockOrganizationsClient:
    def get_organization(self, organization_id):
        if organization_id == MOCK_USER_DATA["organization_id"]:
            return MockOrganization(MOCK_ORGANIZATION_DATA)
        raise Exception(f"Organization not found: {organization_id}")

    def list_organizations(self, **kwargs):
        class MockOrganizationList:
            def __init__(self):
                self.data = [MockOrganization(MOCK_ORGANIZATION_DATA)]
                self.list_metadata = {"after": None, "before": None}

        return MockOrganizationList()


# Mock Organization object
class MockOrganization:
    def __init__(self, org_data):
        for key, value in org_data.items():
            setattr(self, key, value)


# Mock UserManagement client for development mode
class MockUserManagementClient:
    def load_sealed_session(self, sealed_session, cookie_password):
        return MockSession()


# User-like class for development mode
class MockUser:
    def __init__(self, user_data):
        for key, value in user_data.items():
            setattr(self, key, value)


# Mock session class for development mode
class MockSession:
    def __init__(self, user_data=None):
        self.user_data = user_data or MOCK_USER_DATA

    def authenticate(self):
        # Create a mock response object that mimics WorkOS's response
        class MockAuthResponse:
            def __init__(self, user_data):
                self.authenticated = True
                self.user = MockUser(user_data)
                self.organization_id = user_data.get("organization_id")
                self.role = user_data.get("role")
                self.sealed_session = "mock_sealed_session"

        return MockAuthResponse(self.user_data)

    def refresh(self):
        # Just return the same mock response
        return self.authenticate()


def set_mock_user_context():
    """Set mock user context in Flask's g object for development."""
    mock_session = MockSession()
    auth_response = mock_session.authenticate()
    g.user = auth_response.user  # This is now a MockUser object with attributes
    g.role = auth_response.role
    g.organization_id = auth_response.organization_id
