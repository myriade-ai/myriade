# Myriade BI - Installation Guide

This script will install Myriade BI on your server.

## Prerequisites

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **Firewall**: Ports 80 and 443 must be open and accessible

## Recommended Infrastructure

- Machine type:
  - GCP: e2-standard-2 or higher
  - Azure: Standard_D2s_v3 or higher
  - AWS: t3.medium or higher
- vCPUs: 2 vCPUs minimum (4 vCPUs recommended)
- Memory: 4 GB RAM minimum (8 GB recommended)
- Boot disk: 10 GB SSD persistent minimum (50 GB recommended)

## Usage

Run the following command to install Myriade BI on your server:

```bash
curl -fsSL https://install.myriade.ai | bash -s -- myriade.YOUR_DOMAIN.com
```

This script will:

1. Download and extract Myriade BI
2. Install dependencies (Docker, Docker Compose, Nginx)
3. Create initial HTTP Nginx configuration (app accessible immediately)
4. Start Myriade BI containers
5. Prompt for SSL certificate setup with three options:
   - **Let's Encrypt** (recommended for public servers)
   - **Manual certificate** (for enterprise certificates)
   - **Self-signed certificate** (for testing/private networks)

## DNS Setup

DNS can be configured **before or after** running the installation script.

- **Before installation**: The script will automatically offer Let's Encrypt SSL certificates
- **After installation**: The app will be accessible via HTTP, and you can run the SSL script later

To use Let's Encrypt, your domain's A record must point to your server's IP address.

## SSL Certificate Setup

If you skipped SSL during installation or need to reconfigure it, run:

```bash
~/myriade-bi/setup/install_certificate.sh myriade.YOUR_DOMAIN.com
```

### SSL Options

| Option | Best For |
|--------|----------|
| Let's Encrypt | Public servers with DNS configured |
| Manual certificate | Enterprise/CA-signed certificates |
| Self-signed | Testing, development, private networks |

## Troubleshooting

### Check application status
```bash
cd ~/myriade-bi && sudo docker compose ps
```

### View application logs
```bash
cd ~/myriade-bi && sudo docker compose logs -f myriade
```

### Restart the application
```bash
cd ~/myriade-bi && sudo docker compose restart
```

### Check Nginx status
```bash
sudo systemctl status nginx
sudo nginx -t
```
