# Myriade BI - Installation Guide

> Looking to **try Myriade** without provisioning a server? Run this on any
> OS with Docker (macOS, Windows, Linux):
>
> ```bash
> docker run -p 8080:8080 -v myriade-data:/app/data myriadeai/myriade:latest
> ```
>
> Open <http://localhost:8080>. Uses SQLite, no setup required. The guide
> below covers the full Postgres-backed self-hosted install for production.

## Prerequisites

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **Firewall**: Port 8080 (quick start) or ports 80/443 (with domain)

## Recommended Infrastructure

- Machine type:
  - GCP: e2-standard-2 or higher
  - Azure: Standard_D2s_v3 or higher
  - AWS: t3.medium or higher
- vCPUs: 2 vCPUs minimum (4 vCPUs recommended)
- Memory: 4 GB RAM minimum (8 GB recommended)
- Boot disk: 10 GB SSD persistent minimum (50 GB recommended)

## Quick Start

```bash
curl -fsSL https://install.myriade.ai | bash
```

This installs Docker, downloads Myriade BI to `/opt/myriade`, and starts it on port 8080.

By default, the script uses the server's **private/internal IP** — this works for:
- On-premise / private network deployments
- Cloud VPCs where users access from within the network

For servers directly exposed to the internet (public IP accessible), use:

```bash
curl -fsSL https://install.myriade.ai | bash -s -- --public-ip
```

Access your instance at: `http://YOUR_SERVER_IP:8080`

## Adding Domain & SSL

Once your instance is running, add a domain and SSL certificate:

```bash
sudo /opt/myriade/setup/install_certificate.sh YOUR_DOMAIN.com
```

This will:
- Install and configure Nginx as a reverse proxy
- Switch Docker from public port 8080 to localhost-only
- Set up SSL certificates
- Update the `HOST` variable in `.env`

### DNS Setup

Before running the certificate script, create an A record pointing your domain to the server IP:

| Provider | Record type | Name | Value |
|----------|------------|------|-------|
| Route 53 | A | `myriade` | `YOUR_SERVER_IP` |
| Cloudflare | A | `myriade` | `YOUR_SERVER_IP` |
| Other | A | `myriade.yourdomain.com` | `YOUR_SERVER_IP` |

Verify propagation: `dig myriade.yourdomain.com`

### Firewall

Ports 80 and 443 must be open for SSL to work. On AWS, add inbound rules to your Security Group:
- HTTP: TCP 80, source 0.0.0.0/0
- HTTPS: TCP 443, source 0.0.0.0/0

### SSL Options

| Option | Best For |
|--------|----------|
| Let's Encrypt | Public servers with DNS configured |
| Manual certificate | Enterprise/CA-signed certificates |
| Self-signed | Testing, development, private networks |

## Updating Myriade

To update to the latest version:

```bash
sudo /opt/myriade/setup/update.sh
```

To update to a specific version:

```bash
sudo /opt/myriade/setup/update.sh 1.165.0
```

To list available versions:

```bash
sudo /opt/myriade/setup/update.sh versions
```

Before updating the application, the script checks the maintained
[`setup/update.sh` on the public repository's `master` branch](https://github.com/myriade-ai/myriade/blob/master/setup/update.sh).
If it has changed, it downloads the script over HTTPS, checks its updater marker,
self-update protocol and Bash syntax, saves the current copy as
`setup/update.sh.previous`, and replaces it atomically. It then executes the new
script with the original arguments and environment, without downloading again.
The updater follows `master` even when an older application version is requested.
The `versions` command does not update the script.

The script then pulls the requested Docker image, restarts the container, and
waits for the health check to pass. Database migrations are applied automatically
on startup.

If downloading, validating or installing the updater fails, the update stops
before touching services. For a restricted network, a locally maintained script,
or a deliberate recovery using the saved copy, disable the self-update explicitly:

```bash
sudo env MYRIADE_SKIP_SELF_UPDATE=1 /opt/myriade/setup/update.sh
# Or use the previous updater, if a new one has a regression:
sudo env MYRIADE_SKIP_SELF_UPDATE=1 /opt/myriade/setup/update.sh.previous
```

Local edits to `update.sh` are replaced during automatic updates; use environment
variables for configuration, or the opt-out above for a managed local copy.

If the Compose stack includes `autoheal`, the updater stops it before restarting
Myriade so that slow migrations can finish without being interrupted. Autoheal
starts again only once Myriade responds on `/health` and its Docker healthcheck
is healthy (when configured). The updater allows 30 minutes for startup by
default. To allow up to one hour:

```bash
sudo env MYRIADE_UPDATE_TIMEOUT=3600 /opt/myriade/setup/update.sh
```

`MYRIADE_UPDATE_TIMEOUT` is supplied through the script's environment, in seconds
(1–86400). If startup fails, the deadline expires, or the update is interrupted,
the script exits unsuccessfully and leaves autoheal stopped if it was suspended.
The application is not stopped or rolled back: a migration may still be running.
From the installation directory, inspect `sudo docker compose logs -f myriade`
and `sudo docker compose ps myriade`. Once the application is healthy, resume
supervision with `sudo docker compose up -d --no-deps autoheal`.

This protection applies to the stack's `autoheal` service when using this updater;
external supervisors and direct `docker compose up` commands are unaffected.
Existing installations must receive this updated `setup/update.sh`; pulling a
new application image alone does not replace the host's update script. Once the
self-updating version is published on `master`, install it once on existing hosts:

```bash
updater_file="$(mktemp)" &&
  curl -fsSL --proto '=https' --proto-redir '=https' \
    --connect-timeout 10 --max-time 30 \
    https://raw.githubusercontent.com/myriade-ai/myriade/master/setup/update.sh \
    -o "$updater_file" &&
  bash -n "$updater_file" &&
  sudo install -m 755 "$updater_file" /opt/myriade/setup/update.sh
rm -f "$updater_file"
```

Adjust the installation path if needed. Subsequent normal update commands will
refresh the script automatically. New installations receive it through the
installation release archive once that archive includes the updated script.

## Troubleshooting

### Check application status
```bash
sudo docker compose -f /opt/myriade/docker-compose.yml ps
```

### View application logs
```bash
sudo docker compose -f /opt/myriade/docker-compose.yml logs -f myriade
```

### Restart the application
```bash
sudo docker compose -f /opt/myriade/docker-compose.yml restart
```

### Check Nginx status
```bash
sudo systemctl status nginx
sudo nginx -t
```
