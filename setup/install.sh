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
docker compose ps

echo ""
print_message "Installation complete! 🎉"
