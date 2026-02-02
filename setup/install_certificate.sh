#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print messages
print_message() {
    echo -e "${GREEN}=====> $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

print_error() {
    echo -e "${RED}Error: $1${NC}"
}

print_info() {
    echo -e "${BLUE}Info: $1${NC}"
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

DOMAIN_NAME="$1"

# Determine installation directory (look for nginx.conf template)
if [ -f "./setup/nginx.conf" ]; then
    INSTALL_DIR="$(pwd)"
elif [ -f "../setup/nginx.conf" ]; then
    INSTALL_DIR="$(cd .. && pwd)"
elif [ -f "$HOME/myriade-bi/setup/nginx.conf" ]; then
    INSTALL_DIR="$HOME/myriade-bi"
else
    INSTALL_DIR="$HOME/myriade-bi"
fi

echo ""
echo "============================================================"
echo "  Myriade BI - SSL Certificate Installation"
echo "============================================================"
echo ""

print_info "Domain: $DOMAIN_NAME"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

# Detect if server is on private network using local interface
print_message "Detecting server configuration..."
IS_PRIVATE_IP=false
SERVER_IP=""

# Get local IP from network interfaces (first non-loopback IP)
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
fi

# Check if the local IP is private
if [[ "$LOCAL_IP" =~ ^10\. ]] || [[ "$LOCAL_IP" =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]] || [[ "$LOCAL_IP" =~ ^192\.168\. ]]; then
    IS_PRIVATE_IP=true
    SERVER_IP="$LOCAL_IP"
else
    # Try to get public IP for DNS verification
    SERVER_IP=$(curl -s --connect-timeout 5 ifconfig.me || curl -s --connect-timeout 5 icanhazip.com || echo "$LOCAL_IP")
fi

echo "  Server IP: $SERVER_IP"
if [ "$IS_PRIVATE_IP" = true ]; then
    echo "  Network: Private (VPN/Internal)"
else
    echo "  Network: Public (Internet)"
fi
echo ""

# Function to install nginx config from template
install_nginx_config() {
    local cert_path="$1"
    local key_path="$2"

    print_message "Updating Nginx configuration..."

    # Ensure directories exist
    sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

    # Backup existing config if present
    if [ -f "/etc/nginx/sites-available/myriade" ]; then
        sudo cp /etc/nginx/sites-available/myriade /etc/nginx/sites-available/myriade.backup
    fi

    # Check if template exists
    if [ -f "${INSTALL_DIR}/setup/nginx.conf" ]; then
        # Use template and substitute placeholders
        sudo sed -e "s|__DOMAIN__|${DOMAIN_NAME}|g" \
                 -e "s|__SSL_CERT__|${cert_path}|g" \
                 -e "s|__SSL_KEY__|${key_path}|g" \
                 "${INSTALL_DIR}/setup/nginx.conf" > /tmp/myriade-nginx.conf
        sudo mv /tmp/myriade-nginx.conf /etc/nginx/sites-available/myriade
    else
        # Fallback to inline config if template not found
        print_warning "Template not found, using inline configuration"
        sudo tee /etc/nginx/sites-available/myriade > /dev/null <<EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME};
    return 301 https://\$host\$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name ${DOMAIN_NAME};

    ssl_certificate ${cert_path};
    ssl_certificate_key ${key_path};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 10M;

    location /api/events {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }
}
EOF
    fi

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/myriade /etc/nginx/sites-enabled/myriade
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test and reload
    if sudo nginx -t; then
        sudo systemctl reload nginx
        return 0
    else
        print_error "Nginx configuration test failed"
        if [ -f "/etc/nginx/sites-available/myriade.backup" ]; then
            sudo mv /etc/nginx/sites-available/myriade.backup /etc/nginx/sites-available/myriade
            sudo systemctl reload nginx
        fi
        return 1
    fi
}

# Function to generate self-signed certificate
generate_self_signed() {
    print_message "Generating self-signed certificate..."

    sudo mkdir -p /etc/ssl/certs /etc/ssl/private

    # Generate certificate (valid for 365 days)
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "/etc/ssl/private/${DOMAIN_NAME}.key" \
        -out "/etc/ssl/certs/${DOMAIN_NAME}.crt" \
        -subj "/CN=${DOMAIN_NAME}/O=Myriade BI/C=CA" \
        -addext "subjectAltName=DNS:${DOMAIN_NAME}"

    sudo chmod 644 "/etc/ssl/certs/${DOMAIN_NAME}.crt"
    sudo chmod 600 "/etc/ssl/private/${DOMAIN_NAME}.key"

    print_message "Self-signed certificate generated successfully"
    echo ""
    print_warning "This is a self-signed certificate. Browsers will show a security warning."
    print_info "For production use, consider using Let's Encrypt or your own CA-signed certificate."
}

# Show menu based on IP type
if [ "$IS_PRIVATE_IP" = true ]; then
    print_warning "Private IP detected - Let's Encrypt cannot be used"
    echo ""
    echo "Please select an option:"
    echo "  1) I have my own SSL certificates ready to upload"
    echo "  2) Generate self-signed certificates (for testing)"
    echo "  3) Exit"
    echo ""
    read -p "Enter your choice (1-3): " CHOICE

    # Remap choices for private IP case (no Let's Encrypt option)
    if [ "$CHOICE" = "1" ]; then CHOICE="manual"; fi
    if [ "$CHOICE" = "2" ]; then CHOICE="self-signed"; fi
    if [ "$CHOICE" = "3" ]; then CHOICE="exit"; fi
else
    # Check DNS first
    print_message "Checking DNS configuration..."
    if command -v dig &> /dev/null; then
        DNS_IP=$(dig +short "$DOMAIN_NAME" | head -n1)
    else
        print_warning "dig not found, installing dnsutils..."
        sudo apt install -y dnsutils
        DNS_IP=$(dig +short "$DOMAIN_NAME" | head -n1)
    fi

    if [ -z "$DNS_IP" ]; then
        print_warning "DNS lookup failed for $DOMAIN_NAME"
        DNS_READY=false
    elif [ "$DNS_IP" != "$SERVER_IP" ]; then
        print_warning "DNS mismatch detected:"
        echo "  Server IP: $SERVER_IP"
        echo "  DNS IP:    $DNS_IP"
        DNS_READY=false
    else
        print_message "DNS correctly configured: $DOMAIN_NAME -> $SERVER_IP"
        DNS_READY=true
    fi
    echo ""

    if [ "$DNS_READY" = true ]; then
        echo "Please select an option:"
        echo "  1) Obtain certificate from Let's Encrypt (recommended)"
        echo "  2) Install my own SSL certificates"
        echo "  3) Generate self-signed certificates (for testing)"
        echo "  4) Exit"
        echo ""
        read -p "Enter your choice (1-4): " CHOICE
    else
        echo "Please select an option:"
        echo "  1) Fix DNS and retry (DNS must point to $SERVER_IP)"
        echo "  2) Install my own SSL certificates"
        echo "  3) Generate self-signed certificates (for testing)"
        echo "  4) Exit"
        echo ""
        read -p "Enter your choice (1-4): " CHOICE

        # Map choice 1 to DNS setup info
        if [ "$CHOICE" = "1" ]; then
            echo ""
            print_info "Please configure your domain's A record to point to: $SERVER_IP"
            print_info "After DNS propagation (5-30 minutes), retry this script"
            echo ""
            exit 0
        fi
        # Remap choices for DNS not ready case
        if [ "$CHOICE" = "2" ]; then CHOICE="manual"; fi
        if [ "$CHOICE" = "3" ]; then CHOICE="self-signed"; fi
        if [ "$CHOICE" = "4" ]; then CHOICE="exit"; fi
    fi
fi

# Process user choice
case $CHOICE in
    1)
        # Let's Encrypt installation
        echo ""
        print_message "Installing Let's Encrypt certificate..."

        # Check if certbot is installed
        if ! command -v certbot &> /dev/null; then
            print_message "Installing Certbot..."
            sudo apt update -y
            sudo apt install -y certbot python3-certbot-nginx
        fi

        # Prompt for email
        read -p "Enter email for Let's Encrypt notifications (optional, press Enter to skip): " EMAIL

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

            # Enable auto-renewal
            if ! sudo systemctl is-enabled certbot.timer > /dev/null 2>&1; then
                sudo systemctl enable certbot.timer
                sudo systemctl start certbot.timer
                print_message "Auto-renewal enabled"
            fi

            # Ensure site is enabled
            sudo ln -sf /etc/nginx/sites-available/myriade /etc/nginx/sites-enabled/myriade
            sudo rm -f /etc/nginx/sites-enabled/default

            # Test HTTPS
            echo ""
            print_message "Testing HTTPS connection..."
            sleep 2
            if curl -sI "https://$DOMAIN_NAME" > /dev/null 2>&1; then
                print_message "HTTPS is working correctly!"
                echo ""
                print_message "Your application is now available at: https://$DOMAIN_NAME"
            else
                print_warning "HTTPS test failed. Please check nginx logs:"
                echo "  sudo journalctl -u nginx -n 50"
            fi
        else
            print_error "Failed to obtain certificate from Let's Encrypt"
            echo ""
            print_info "Common issues:"
            echo "  - Port 80/443 blocked by firewall"
            echo "  - Domain already has a certificate"
            echo "  - Rate limit reached (5 per week)"
            exit 1
        fi
        ;;
    2|manual)
        # Manual certificate installation
        echo ""
        print_message "Manual certificate installation"
        echo ""
        print_info "You need two files:"
        echo "  1. Full chain certificate (usually .crt or .pem)"
        echo "  2. Private key (usually .key)"
        echo ""

        # Ask for certificate file
        read -p "Enter the full path to your certificate file: " CERT_FILE
        if [ ! -f "$CERT_FILE" ]; then
            print_error "Certificate file not found: $CERT_FILE"
            exit 1
        fi

        # Ask for key file
        read -p "Enter the full path to your private key file: " KEY_FILE
        if [ ! -f "$KEY_FILE" ]; then
            print_error "Key file not found: $KEY_FILE"
            exit 1
        fi

        # Copy files to standard locations
        print_message "Installing certificate files..."
        sudo mkdir -p /etc/ssl/certs /etc/ssl/private
        sudo cp "$CERT_FILE" "/etc/ssl/certs/${DOMAIN_NAME}.crt"
        sudo cp "$KEY_FILE" "/etc/ssl/private/${DOMAIN_NAME}.key"
        sudo chmod 644 "/etc/ssl/certs/${DOMAIN_NAME}.crt"
        sudo chmod 600 "/etc/ssl/private/${DOMAIN_NAME}.key"

        # Install nginx config
        if install_nginx_config "/etc/ssl/certs/${DOMAIN_NAME}.crt" "/etc/ssl/private/${DOMAIN_NAME}.key"; then
            # Test HTTPS
            echo ""
            print_message "Testing HTTPS connection..."
            sleep 2
            if curl -sIk "https://$DOMAIN_NAME" > /dev/null 2>&1; then
                print_message "HTTPS is working correctly!"
                echo ""
                print_message "Your application is now available at: https://$DOMAIN_NAME"
            else
                print_warning "HTTPS test failed. Please check:"
                echo "  1. Certificate files are valid"
                echo "  2. Certificate matches your domain"
                echo "  3. Nginx logs: sudo journalctl -u nginx -n 50"
            fi
        else
            exit 1
        fi
        ;;
    3|self-signed)
        # Self-signed certificate
        echo ""
        generate_self_signed

        # Install nginx config
        if install_nginx_config "/etc/ssl/certs/${DOMAIN_NAME}.crt" "/etc/ssl/private/${DOMAIN_NAME}.key"; then
            echo ""
            print_message "Testing HTTPS connection..."
            sleep 2
            if curl -sIk "https://$DOMAIN_NAME" > /dev/null 2>&1; then
                print_message "HTTPS is working (with self-signed certificate)!"
                echo ""
                print_warning "Browsers will show a security warning for self-signed certificates."
                print_message "Your application is now available at: https://$DOMAIN_NAME"
            else
                print_warning "HTTPS test failed. Please check nginx logs:"
                echo "  sudo journalctl -u nginx -n 50"
            fi
        else
            exit 1
        fi
        ;;
    4|exit)
        echo ""
        print_info "Exiting without changes"
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_message "SSL certificate installation complete!"
echo ""
