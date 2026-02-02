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
    echo "Usage: $0 <domain_name>"
    echo ""
    echo "Example:"
    echo "  $0 myriade.entreprise.com"
    exit 1
fi

# Set the domain name from the first argument
DOMAIN_NAME="$1"
SSL_SUCCESS=false

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
DOWNLOAD_URL="${MYRIADE_DOWNLOAD_URL:-https://install.myriade.ai/myriade-bi-latest.tar.gz}"

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download and extract
print_message "Downloading Myriade BI from $DOWNLOAD_URL..."
if ! curl -fsSL "$DOWNLOAD_URL" -o myriade.tar.gz; then
    print_error "Failed to download Myriade BI. Please check your internet connection."
    exit 1
fi

print_message "Extracting files..."
tar -xzf myriade.tar.gz --strip-components=1
rm myriade.tar.gz

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
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $VERSION_CODENAME stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
elif [ "$OS" = "ubuntu" ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg
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

# Create initial HTTP nginx configuration (so app is accessible before SSL setup)
print_message "Configuring Nginx for HTTP access..."
sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

sudo tee /etc/nginx/sites-available/myriade > /dev/null <<EOF
# HTTP server for Myriade BI
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Request limits
    client_max_body_size 10M;

    # SSE endpoint
    location /api/events {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;

        # SSE-specific settings
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Ensure chunked transfer works
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # Main proxy
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;

        # WebSocket/Socket.io support
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

# Enable the site and remove default
sudo ln -sf /etc/nginx/sites-available/myriade /etc/nginx/sites-enabled/myriade
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
if sudo nginx -t; then
    sudo systemctl reload nginx
    print_message "Nginx configured successfully"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

# Configure environment variables
print_message "Configuring environment variables..."

# Generate a secure random password if not provided
if [ -z "$POSTGRES_PASSWORD" ]; then
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    print_message "Generated secure database password"
else
    print_message "Using provided database password"
fi

# Generate credential encryption key if not provided (Fernet format: URL-safe base64)
if [ -z "$CREDENTIAL_ENCRYPTION_KEY" ]; then
    # Fernet keys are 32 bytes, URL-safe base64 encoded (44 chars)
    CREDENTIAL_ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n' | tr '+/' '-_')
    print_message "Generated credential encryption key"
fi

# Create .env file for Docker Compose
cat > .env << EOF
POSTGRES_DB=${POSTGRES_DB:-myriade}
POSTGRES_USER=${POSTGRES_USER:-myriade}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
HOST=${DOMAIN_NAME}
CREDENTIAL_ENCRYPTION_KEY=${CREDENTIAL_ENCRYPTION_KEY}
EOF

chmod 600 .env
print_message "Environment configuration saved to .env file"

# Start Docker Compose
print_message "Starting Myriade BI with Docker Compose..."
if sudo docker compose up -d; then
    print_message "Docker containers started successfully"
else
    print_error "Failed to start Docker containers"
    exit 1
fi

# Wait for application to be ready with health check polling
print_message "Waiting for application to start..."
MAX_ATTEMPTS=60
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        print_message "Application is healthy and responding on port 8080"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        print_warning "Application may not be ready yet. Check logs with: sudo docker compose logs myriade"
    else
        sleep 2
    fi
done

echo ""

# Run SSL certificate installation
print_message "Starting SSL certificate setup..."
echo ""

if [ -f "${INSTALL_DIR}/setup/install_certificate.sh" ]; then
    if bash "${INSTALL_DIR}/setup/install_certificate.sh" "${DOMAIN_NAME}"; then
        SSL_SUCCESS=true
    else
        SSL_SUCCESS=false
        print_warning "SSL certificate setup did not complete successfully"
    fi
else
    print_error "Certificate installation script not found"
    SSL_SUCCESS=false
fi

# Print success message
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ✅ Myriade BI Installation Complete!                         ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$SSL_SUCCESS" = false ]; then
    print_warning "SSL certificate was not configured during installation"
    echo ""
    print_message "To set up SSL certificate for HTTPS, run:"
    echo ""
    echo "  ${INSTALL_DIR}/setup/install_certificate.sh ${DOMAIN_NAME}"
    echo ""
    print_warning "🌐 Application is currently running at: http://${DOMAIN_NAME}"
    echo ""
fi

# Display running containers
print_message "Running containers:"
sudo docker compose ps

echo ""
print_message "Installation complete! 🎉"
