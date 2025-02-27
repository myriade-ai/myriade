# Authentication System

This directory contains the authentication system for the application, which uses WorkOS for user management and authentication.

## Development Mode

For local development without requiring a WorkOS account, you can use the development mode. This mode provides a mock authentication system that simulates WorkOS authentication.

### How to Enable Development Mode

1. Set the `OFFLINE_MODE` environment variable to `true` in your `.env` file:

```
OFFLINE_MODE=true
```

2. When in development mode, you don't need to provide `WORKOS_API_KEY` or `WORKOS_CLIENT_ID`.

3. The system will automatically use a mock user.

### Customizing the Mock Data

If you need to customize the mock user, you can modify the `MOCK_USER_DATA` dictionary in `mock.py`. The system will automatically convert this dictionary into a `MockUser` object with attributes that match the keys in the dictionary.

For example, `MOCK_USER_DATA["id"]` becomes accessible as `user.id` in your application code.

Similarly, you can customize the mock organization by modifying the `MOCK_ORGANIZATION_DATA` dictionary.

### Mock WorkOS Client

In development mode, a `MockWorkOSClient` is provided that implements the following functionality:

- `workos_client.organizations.get_organization(organization_id)` - Returns a mock organization
- `workos_client.organizations.list_organizations()` - Returns a list containing the mock organization
- `workos_client.user_management.load_sealed_session()` - Returns a mock session

This allows your code to use the WorkOS client API without changes in both development and production environments.

## Production Mode

For production, make sure to:

1. Set `OFFLINE_MODE` to `false` or remove it from your environment variables
2. Provide valid `WORKOS_API_KEY` and `WORKOS_CLIENT_ID` values

## Authentication Flow

The authentication system provides:

1. A `with_auth` decorator for protecting API routes
2. Socket authentication for WebSocket connections
3. Session management with automatic refreshing

All of these features work in both development and production modes.
