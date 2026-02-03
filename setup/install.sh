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

# Detect operating system
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Linux*)
        # Will check for Debian/Ubuntu later
        ;;
    Darwin*)
        echo ""
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║  macOS Detected - Local Development Setup                      ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "This installer is designed for Ubuntu/Debian servers."
        echo "For macOS local development, use Docker Compose directly:"
        echo ""
        echo "  # 1. Download and extract"
        echo "  curl -fsSL https://install.myriade.ai/myriade-bi-latest.tar.gz | tar -xz"
        echo "  cd myriade-bi"
        echo ""
        echo "  # 2. Set password and start"
        echo "  export POSTGRES_PASSWORD=your_secure_password"
        echo "  docker compose up -d"
        echo ""
        echo "  # 3. Open http://localhost:8080"
        echo ""
        echo "For production deployment, run this script on an Ubuntu/Debian server."
        echo ""
        exit 0
        ;;
    *)
        print_error "Unsupported operating system: $OS_TYPE"
        echo "This installer supports Ubuntu 20.04+ and Debian 11+"
        exit 1
        ;;
esac

print_message "Starting Myriade BI installation..."
echo ""

# Update and install prerequisites
print_message "Updating package index and installing prerequisites..."
sudo apt update -y
sudo apt install -y ca-certificates curl gnupg lsb-release unzip wget

# Download latest Myriade BI release
print_message "Downloading latest Myriade BI release..."
INSTALL_DIR="/opt/myriade"
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

# Add current user to the docker group (skip if running as root — root already has access)
if [ "$EUID" -ne 0 ]; then
    print_message "Adding current user to the docker group..."
    sudo usermod -aG docker $USER
fi

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

# Get server IP for HOST configuration
SERVER_IP=$(curl -s --connect-timeout 5 ifconfig.me || curl -s --connect-timeout 5 icanhazip.com || hostname -I 2>/dev/null | awk '{print $1}')

# Configure Docker to bind directly to port 8080 (no nginx for quick start)
print_message "Configuring Docker for direct access on port 8080..."
sed -i "s|127.0.0.1:8080:8080|0.0.0.0:8080:8080|g" docker-compose.yml

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
HOST=http://${SERVER_IP}:8080
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

# Print success message
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ✅ Myriade BI Installation Complete!                         ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
print_message "🌐 Access Myriade BI at: http://${SERVER_IP}:8080"
echo ""
print_message "To add a domain and SSL certificate, run:"
echo ""
echo "  ${INSTALL_DIR}/setup/install_certificate.sh YOUR_DOMAIN.com"
echo ""

# Display running containers
print_message "Running containers:"
sudo docker compose ps

echo ""
print_message "Installation complete! 🎉"
