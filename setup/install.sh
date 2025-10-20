#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print messages
print_message() {
    echo -e "${GREEN}=====> $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if domain name is provided
if [ $# -eq 0 ]; then
    print_error "Please provide a domain name."
    echo "Usage: $0 <domain_name> [email]"
    echo ""
    echo "Examples:"
    echo "  $0 myriade.entreprise.com"
    echo "  $0 myriade.entreprise.com admin@entreprise.com"
    exit 1
fi

# Set the domain name from the first argument
DOMAIN_NAME="$1"
EMAIL="${2:-}" # Optional email for Let's Encrypt

# SSL setup tracking flags
SSL_CONFIGURED=false
DNS_READY=false
IS_PRIVATE_IP=false

# Validate domain name format
if ! [[ "$DOMAIN_NAME" =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
    print_error "Invalid domain name format: $DOMAIN_NAME"
    exit 1
fi

print_message "Starting Myriade BI installation for domain: $DOMAIN_NAME"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

# Update and install prerequisites
print_message "Updating package index and installing prerequisites..."
sudo apt update -y
sudo apt install -y ca-certificates curl gnupg lsb-release unzip wget

# Download latest Myriade BI release
print_message "Downloading latest Myriade BI release..."
INSTALL_DIR="$HOME/myriade-bi"
GITHUB_REPO="${GITHUB_REPO:-myriade-ai/myriade}"  # Allow override with env var
RELEASE_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Get latest release info
print_message "Fetching release information from GitHub..."
RELEASE_INFO=$(curl -s "$RELEASE_URL")
DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep -o "https://github.com/${GITHUB_REPO}/archive/refs/tags/[^\"]*\.zip" | head -1)

# Fallback to master branch if no releases exist
if [ -z "$DOWNLOAD_URL" ]; then
    print_warning "No releases found, downloading from master branch..."
    DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/archive/refs/heads/master.zip"
    TAG_NAME="master"
else
    TAG_NAME=$(echo "$RELEASE_INFO" | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4)
    print_message "Found release: $TAG_NAME"
fi

# Download and extract
print_message "Downloading Myriade BI..."
wget -q --show-progress "$DOWNLOAD_URL" -O myriade.zip

print_message "Extracting files..."
unzip -q myriade.zip
rm myriade.zip

# Move files to installation directory
EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "myriade-*" -o -name "myriade" | head -1)
if [ -n "$EXTRACTED_DIR" ] && [ "$EXTRACTED_DIR" != "." ]; then
    mv "$EXTRACTED_DIR"/* . 2>/dev/null || true
    mv "$EXTRACTED_DIR"/.* . 2>/dev/null || true
    rmdir "$EXTRACTED_DIR" 2>/dev/null || true
fi

# Verify required files exist
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found in release. Installation cannot continue."
    exit 1
fi

# Ensure helper scripts are executable
if [ -f "setup/install_certificate.sh" ]; then
    chmod +x setup/install_certificate.sh
fi

print_message "Myriade BI downloaded successfully to: $INSTALL_DIR"
echo ""

# Return to original directory for rest of installation
cd "$INSTALL_DIR"

# Detect OS for Docker repo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION_CODENAME=$(lsb_release -cs)
else
    print_error "Cannot detect OS. /etc/os-release not found."
    exit 1
fi

print_message "Detected OS: $OS $VERSION_CODENAME"

# Remove old Docker installations
print_message "Removing old Docker installations if they exist..."
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Set up Docker's official GPG key (if not already set up)
if [ ! -d /etc/apt/keyrings ]; then
    print_message "Adding Docker's official GPG key..."
    sudo install -m 0755 -d /etc/apt/keyrings
fi

# Select correct Docker repo based on OS
if [ "$OS" = "debian" ]; then
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $VERSION_CODENAME stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
elif [ "$OS" = "ubuntu" ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
else
    print_error "Unsupported OS: $OS. Only Debian and Ubuntu are supported."
    exit 1
fi

sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Update the package index again
print_message "Updating package index with Docker repository..."
sudo apt update -y

# Install Docker
print_message "Installing Docker..."
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to the docker group
print_message "Adding current user to the docker group..."
sudo usermod -aG docker $USER

# Start and enable Docker service
print_message "Starting and enabling Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

# Verify Docker installation
if docker --version > /dev/null 2>&1; then
    print_message "Docker installed successfully: $(docker --version)"
else
    print_error "Docker installation failed"
    exit 1
fi

# Install Nginx
print_message "Installing Nginx..."
sudo apt install -y nginx

# Stop nginx temporarily to avoid port conflicts
sudo systemctl stop nginx

# Create initial HTTP-only Nginx configuration
print_message "Creating initial Nginx configuration (HTTP only)..."
sudo tee /etc/nginx/sites-available/myriade > /dev/null <<EOF
# Initial HTTP configuration for Let's Encrypt validation
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME};

    # Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Proxy to Myriade application
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Socket.io support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout settings for long AI requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/myriade /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_message "Testing Nginx configuration..."
if sudo nginx -t; then
    print_message "Nginx configuration is valid"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

# Start Nginx
print_message "Starting Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Install Certbot
print_message "Installing Certbot for Let's Encrypt..."
sudo apt install -y certbot python3-certbot-nginx

# Check if server has a private IP
print_message "Checking server network configuration..."
SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "unknown")

if [[ "$SERVER_IP" =~ ^10\. ]] || [[ "$SERVER_IP" =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]] || [[ "$SERVER_IP" =~ ^192\.168\. ]]; then
    IS_PRIVATE_IP=true
    print_warning "Private IP detected: $SERVER_IP"
    print_warning "Let's Encrypt cannot be used with private IPs."
    print_message "Installation will continue. Manual certificate setup instructions will be provided."
else
    # Verify DNS is pointing to this server
    print_message "Verifying DNS configuration for $DOMAIN_NAME..."
    # Install dig if not installed
    if ! command -v dig &> /dev/null; then
        print_message "Installing dig..."
        sudo apt install -y dnsutils
    fi

    DNS_IP=$(dig +short $DOMAIN_NAME | head -n1)

    if [ -z "$DNS_IP" ]; then
        print_warning "DNS lookup failed for $DOMAIN_NAME"
        print_warning "Your domain's A record should point to: $SERVER_IP"
        print_message "Installation will continue. SSL setup instructions will be provided at the end."
    elif [ "$DNS_IP" != "$SERVER_IP" ]; then
        print_warning "DNS mismatch detected:"
        echo "  Server IP: $SERVER_IP"
        echo "  DNS IP:    $DNS_IP"
        print_warning "Let's Encrypt requires DNS to point to this server."
        print_message "Installation will continue. SSL setup instructions will be provided at the end."
    else
        print_message "DNS correctly configured: $DOMAIN_NAME -> $SERVER_IP"
        DNS_READY=true
    fi
fi

# Start Docker Compose
print_message "Starting Myriade BI with Docker Compose..."
if docker compose up -d; then
    print_message "Docker containers started successfully"
else
    print_error "Failed to start Docker containers"
    exit 1
fi

# Wait for application to be ready
print_message "Waiting for application to start (30 seconds)..."
sleep 30

# Check if application is responding
if curl -s http://localhost:8080 > /dev/null; then
    print_message "Application is responding on port 8080"
else
    print_warning "Application may not be ready yet. Check logs with: docker compose logs myriade"
fi

# Setup Let's Encrypt SSL certificate (if DNS is ready and public IP)
if [ "$IS_PRIVATE_IP" = false ] && [ "$DNS_READY" = true ]; then
    print_message "Setting up Let's Encrypt SSL certificate..."

    if [ -z "$EMAIL" ]; then
        read -p "Enter email for Let's Encrypt notifications (optional, press Enter to skip): " EMAIL
    fi

    # Build certbot command
    CERTBOT_CMD="sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos"
    if [ -n "$EMAIL" ]; then
        CERTBOT_CMD="$CERTBOT_CMD --email $EMAIL"
    else
        CERTBOT_CMD="$CERTBOT_CMD --register-unsafely-without-email"
    fi

    # Run certbot
    if $CERTBOT_CMD; then
        print_message "SSL certificate installed successfully!"
        SSL_CONFIGURED=true

        # Test HTTPS
        if curl -s https://$DOMAIN_NAME > /dev/null 2>&1; then
            print_message "HTTPS is working correctly"
        else
            print_warning "HTTPS may not be working yet. Give it a few seconds."
        fi
    else
        print_warning "Failed to obtain SSL certificate from Let's Encrypt"
        print_message "Don't worry - installation will complete and provide manual setup instructions."
    fi
else
    print_message "Skipping automatic SSL setup (DNS not ready or private IP detected)"
fi

# Setup automatic certificate renewal (only if SSL was configured)
if [ "$SSL_CONFIGURED" = true ]; then
    print_message "Setting up automatic certificate renewal..."
    if sudo systemctl is-enabled certbot.timer > /dev/null 2>&1; then
        print_message "Certbot renewal timer already enabled"
    else
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer
        print_message "Certbot will automatically renew certificates"
    fi
fi

# Provide manual SSL setup instructions if needed
if [ "$SSL_CONFIGURED" = false ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║  ⚠️  SSL Certificate Setup Required                           ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    if [ "$IS_PRIVATE_IP" = true ]; then
        print_warning "Private IP detected - Let's Encrypt cannot be used"
        echo ""
        print_message "To set up SSL certificates, run the certificate installation helper:"
        echo ""
        echo "  ${INSTALL_DIR}/setup/install_certificate.sh ${DOMAIN_NAME}"
        echo ""
        print_message "The helper script will guide you through:"
        echo "  • Installing your own SSL certificates"
        echo "  • Generating self-signed certificates (for testing)"
        echo "  • Automatically updating Nginx configuration"
    else
        print_warning "DNS not ready - Let's Encrypt setup was skipped"
        echo ""
        print_message "To complete SSL setup, run the certificate installation helper:"
        echo ""
        echo "  ${INSTALL_DIR}/setup/install_certificate.sh ${DOMAIN_NAME}"
        echo ""
        print_message "The helper script will guide you through:"
        echo "  • Retrying Let's Encrypt (once DNS is ready)"
        echo "  • Installing your own SSL certificates"
        echo "  • Checking DNS configuration"
        echo ""
    fi
    echo ""
fi

# Print success message
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ✅ Myriade BI Installation Complete!                         ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$SSL_CONFIGURED" = true ]; then
    print_message "🌐 Access your application at: https://${DOMAIN_NAME}"
else
    print_warning "🌐 Application is running at: http://${DOMAIN_NAME}"
    print_warning "⚠️  Complete SSL setup (instructions above) to enable HTTPS"
fi

echo ""

# Display running containers
print_message "Running containers:"
docker compose ps

echo ""
print_message "Installation complete! 🎉"
