# Telemetry

## Why

We collect telemetry data to help us improve the product and provide better support:

- **Stability & updates**: Helps us spot outdated or vulnerable versions quickly and show in-app “update available” notices.
- **Product insight**: Aggregated metrics (e.g., number of AI queries, DB back-ends used) guide connector priorities and free-tier quotas.
- **Support**: When you open a ticket, the instance ID and version let us reproduce issues faster.

## What

We collect the following data:

| Field                      | Example                    | Description                                                          |
| -------------------------- | -------------------------- | -------------------------------------------------------------------- |
| `env`                      | `production`               | Environment of the instance.                                         |
| `instance_id`              | `sha256:7e99b8…`           | Deterministic hash generated on first boot; not linked to IP.        |
| `myriade_version`          | `0.7.1`                    | Running backend version.                                             |
| `host_os`                  | `linux`                    | Host operating system (`linux` / `darwin` / `windows`).              |
| `db_backends`              | `["postgres","snowflake"]` | Types of private databases configured (excludes public databases).   |
| `queries_today`            | `123`                      | Count of AI queries executed since midnight UTC.                     |
| `total_assistant_messages` | `456`                      | Total count of assistant messages across all conversations.          |
| `total_user_messages`      | `789`                      | Total count of user messages across all conversations.               |
| `total_users`              | `12`                       | Total count of registered users.                                     |
| `timestamp`                | `2025-07-15T13:45:22Z`     | ISO 8601 timestamp of the send.                                      |

**Never collected:** internal IP addresses, DB connection strings, query contents, end-user personal data.

## Configuration

Telemetry data is automatically sent on application startup and every 24 hours to `https://infra.myriade.ai/app_telemetry`.

If you prefer to disable telemetry collection entirely, you can set the environment variable `MYRIADE_TELEMETRY=off` before starting the application.
