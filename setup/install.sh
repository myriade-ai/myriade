#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Check if domain name is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a domain name."
    echo "Usage: $0 <domain_name>"
    exit 1
fi

# Set the domain name from the first argument
DOMAIN_NAME="$1"

# Function to print messages
print_message() {
    echo "-----> $1"
    echo "-----> $1"
}

# Update and install prerequisites
print_message "Updating package index and installing prerequisites..."
sudo apt update -y
sudo apt install -y ca-certificates curl gnupg

# Remove old Docker installations
print_message "Removing old Docker installations if they exist..."
sudo apt remove -y docker docker-engine docker.io containerd runc || true

# Set up Docker's official GPG key
print_message "Adding Docker's official GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
print_message "Setting up the Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the package index again
print_message "Updating package index with Docker repository..."
sudo apt update -y

# Install Docker
print_message "Installing Docker..."
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to the docker group
print_message "Adding current user to the docker group..."
sudo usermod -aG docker $USER

# Print success message
print_message "Docker installation completed successfully!"
print_message "Please log out and log back in for group changes to take effect."
print_message "You can then run 'docker --version' to verify the installation."


# Add
# Install Docker Compose plugin
print_message "Installing Docker Compose plugin..."
sudo apt install -y docker-compose-plugin

# Start and enable Docker service
print_message "Starting and enabling Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

# Install Nginx
print_message "Installing Nginx..."
sudo apt install -y nginx

# Configure Nginx
print_message "Configuring Nginx..."
sudo envsubst '${DOMAIN_NAME}' < nginx.conf | sudo tee /etc/nginx/sites-available/default > /dev/null

# Start and enable Nginx service
print_message "Starting and enabling Nginx service..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Run Docker Compose
print_message "Running Docker Compose..."
sudo docker compose up -d

# Print success message
print_message "Docker and Nginx installation completed successfully!"
print_message "Please log out and log back in for group changes to take effect."
print_message "You can then run 'docker --version' and 'nginx -v' to verify the installations."

