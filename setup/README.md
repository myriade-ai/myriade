# Myriade BI - Installation Guide

This script will install Myriade BI on your server.

## Prerequisites

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **Firewall**: Ports 80 and 443 must be open and accessible

## Recommended infrastructure

- Machine type:
  - GCP: e2-standard-2 or higher
  - Azure: Standard_D2s_v3 or higher
  - AWS: t3.medium or higher
- vCPUs: 2 vCPUs minimum (4 vCPUs recommended)
- Memory: 4 GB RAM minimum (8 GB recommended)
- Boot disk: 10 GB SSD persistent minimum (50 GB recommended)

## Usage

Run the following command to install Myriade BI on your server.

```bash
curl -fsSL https://install.myriade.ai | bash -s -- myriade.YOUR_DOMAIN.com
```

This script will:

1. Download and extract Myriade BI
2. Install Dependencies (Docker, Docker Compose, Nginx, Certbot, Let's Encrypt certificate)
3. Create initial HTTP-only Nginx configuration (open ports 80 and 443)
4. Start Myriade BI
5. Set up Let's Encrypt SSL certificate (if DNS is ready and public IP)
6. Configure SSL certificate renewal (if SSL certificate was installed)

## DNS Setup

DNS can be configured **before or after** running the installation script.

- **Before installation**: The script will automatically obtain Let's Encrypt SSL certificates
- **After installation**: The installation will complete successfully, and the script will provide commands to set up SSL certificates once DNS is ready

To use Let's Encrypt, your domain's A record must point to your server's IP address.
