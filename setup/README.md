# Myriade BI - Installation Guide

This script will install Myriade BI on your server.

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

## Quick Start (No Domain Required)

Get Myriade BI running in minutes without any domain configuration:

```bash
curl -fsSL https://install.myriade.ai | bash
```

Access your instance at: `http://YOUR_SERVER_IP:8080`

## Production Installation (With Domain & SSL)

For production deployments with HTTPS:

```bash
curl -fsSL https://install.myriade.ai | bash -s -- myriade.YOUR_DOMAIN.com
```

This will:
1. Install Docker, Docker Compose, and Nginx
2. Configure Nginx with your domain
3. Start Myriade BI containers
4. Prompt for SSL certificate setup

## Adding Domain & SSL Later

If you started with the quick install, you can add a domain and SSL anytime:

```bash
/opt/myriade/setup/install_certificate.sh YOUR_DOMAIN.com
```

This will:
- Reconfigure Nginx for ports 80/443
- Set up SSL certificates
- Update your Myriade configuration

### SSL Options

| Option | Best For |
|--------|----------|
| Let's Encrypt | Public servers with DNS configured |
| Manual certificate | Enterprise/CA-signed certificates |
| Self-signed | Testing, development, private networks |

## Troubleshooting

### Check application status
```bash
cd /opt/myriade && sudo docker compose ps
```

### View application logs
```bash
cd /opt/myriade && sudo docker compose logs -f myriade
```

### Restart the application
```bash
cd /opt/myriade && sudo docker compose restart
```

### Check Nginx status
```bash
sudo systemctl status nginx
sudo nginx -t
```
