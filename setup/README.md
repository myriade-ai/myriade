# Myriade BI - Installation Guide

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
