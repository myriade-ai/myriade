# Fly.io Review Apps Setup

This document explains how to set up and use Git branch preview environments with Fly.io for the Myriade application.

## Overview

Review apps automatically create isolated preview environments for each pull request, allowing you to test changes before merging them into the main branch. When a PR is opened, a new Fly.io app is deployed with the changes. When the PR is closed, the app is automatically destroyed.

## Prerequisites

1. **Fly.io Account**: Sign up at [fly.io](https://fly.io)
2. **Fly.io CLI**: Install flyctl locally for initial setup
3. **GitHub Repository**: Your code should be hosted on GitHub

## Initial Setup

### 1. Install Fly.io CLI

```bash
# On macOS
brew install flyctl

# On Linux
curl -L https://fly.io/install.sh | sh

# On Windows
iwr https://fly.io/install.ps1 -useb | iex
```

### 2. Authenticate with Fly.io

```bash
flyctl auth login
```

### 3. Generate API Token

```bash
flyctl auth token
```

Copy the generated token - you'll need it for GitHub Secrets.

### 4. Configure GitHub Secrets

In your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add a new secret named `FLY_API_TOKEN` with the token from step 3
3. Optionally, add these secrets for your application:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)
   - `SENTRY_DSN`: Your Sentry DSN for error tracking (optional)

### 5. Update Fly.io Configuration

The repository includes a `fly.toml` configuration file. Update the following fields:

```toml
# Change 'personal' to your Fly.io organization name
primary_region = "iad"  # Change to your preferred region
```

Available regions: `iad` (US East), `lax` (US West), `lhr` (London), `fra` (Frankfurt), `nrt` (Tokyo), `syd` (Sydney)

## How It Works

### Automatic Deployment

When you create or update a pull request:

1. GitHub Actions triggers the review app workflow
2. A new Fly.io app is created with name `pr-{PR_NUMBER}-myriade`
3. The application is built and deployed using Docker
4. A comment is added to the PR with the preview URL
5. The app is available at `https://pr-{PR_NUMBER}-myriade.fly.dev`

### Automatic Cleanup

When a pull request is closed or merged:

1. The associated Fly.io app is automatically destroyed
2. A comment is added to the PR confirming cleanup
3. No manual intervention required

## Configuration Files

### Key Files Added

- `fly.toml`: Main Fly.io configuration
- `.github/workflows/review-apps.yml`: GitHub Actions workflow
- `.env.fly`: Environment variables for Fly.io deployments
- `service/start-fly.sh`: Fly.io-specific startup script
- `.dockerignore`: Optimizes Docker builds

### Environment Variables

Review apps use the following environment configuration:

- **Database**: SQLite by default (stored in persistent volume)
- **Static Files**: Served from `./static` directory
- **API Keys**: Set via Fly.io secrets (see setup above)

## Managing Secrets

For production deployments, set secrets using flyctl:

```bash
# Set required API key
flyctl secrets set ANTHROPIC_API_KEY=your_key_here

# Set optional keys
flyctl secrets set OPENAI_API_KEY=your_key_here
flyctl secrets set SENTRY_DSN=your_dsn_here
```

## Troubleshooting

### Common Issues

1. **Deployment Fails**: Check GitHub Actions logs for detailed error messages
2. **App Won't Start**: Verify all required environment variables are set
3. **Database Issues**: Check if migrations ran successfully in the logs

### Debugging

View logs for a review app:

```bash
flyctl logs -a pr-123-myriade
```

SSH into a running app:

```bash
flyctl ssh console -a pr-123-myriade
```

### Manual Cleanup

If automatic cleanup fails, manually destroy an app:

```bash
flyctl apps destroy pr-123-myriade --yes
```

## Customization

### Changing App Resources

Edit `fly.toml` to modify:

- Memory allocation (`machines.memory`)
- CPU count (`machines.cpus`)
- Persistent storage size (`mounts.initial_size`)

### Custom Domains

For production deployments, you can configure custom domains:

```bash
flyctl certs create your-domain.com
```

### Scaling

Review apps are configured to auto-stop when idle and auto-start when accessed. For production:

```bash
flyctl scale count 2  # Run 2 instances
flyctl scale memory 2048  # Use 2GB memory
```

## Cost Considerations

- Review apps automatically stop when idle to minimize costs
- Apps are destroyed when PRs are closed
- Persistent volumes are small (1GB) by default
- Consider setting up spending limits in your Fly.io dashboard

## Security

- API keys are stored as GitHub Secrets and Fly.io Secrets
- Apps are isolated per PR
- HTTPS is enforced by default
- Consider IP restrictions for sensitive environments

## Support

For issues with:
- **Fly.io Platform**: Check [Fly.io documentation](https://fly.io/docs/)
- **GitHub Actions**: Review workflow logs in the Actions tab
- **Application Issues**: Check application logs with `flyctl logs`