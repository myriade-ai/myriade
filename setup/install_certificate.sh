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
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
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

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  🔒 Myriade BI - SSL Certificate Installation                 ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

print_info "Domain: $DOMAIN_NAME"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

# Detect server IP and check if private
print_message "Detecting server configuration..."
SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "unknown")
IS_PRIVATE_IP=false

if [[ "$SERVER_IP" =~ ^10\. ]] || [[ "$SERVER_IP" =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]] || [[ "$SERVER_IP" =~ ^192\.168\. ]]; then
    IS_PRIVATE_IP=true
fi

echo "  Server IP: $SERVER_IP"
if [ "$IS_PRIVATE_IP" = true ]; then
    echo "  Network: Private (VPN/Internal)"
else
    echo "  Network: Public (Internet)"
fi
echo ""

# Show menu based on IP type
if [ "$IS_PRIVATE_IP" = true ]; then
    print_warning "Private IP detected - Let's Encrypt cannot be used"
    echo ""
    print_message "You need to install SSL certificates manually."
    echo ""
    echo "Please select an option:"
    echo "  1) I have my own SSL certificates ready to upload"
    echo "  2) I need to generate self-signed certificates (for testing)"
    echo "  3) Exit"
    echo ""
    read -p "Enter your choice (1-3): " CHOICE
else
    # Check DNS first
    print_message "Checking DNS configuration..."
    if command -v dig &> /dev/null; then
        DNS_IP=$(dig +short $DOMAIN_NAME | head -n1)
    else
        print_warning "dig not found, installing dnsutils..."
        sudo apt install -y dnsutils
        DNS_IP=$(dig +short $DOMAIN_NAME | head -n1)
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
        echo "  3) Exit"
        echo ""
        read -p "Enter your choice (1-3): " CHOICE
    else
        echo "Please select an option:"
        echo "  1) Fix DNS and retry Let's Encrypt (DNS must point to $SERVER_IP)"
        echo "  2) I have my own SSL certificates ready to upload"
        echo "  3) Exit"
        echo ""
        read -p "Enter your choice (1-3): " CHOICE
        
        # Map choice 1 to DNS setup then Let's Encrypt
        if [ "$CHOICE" = "1" ]; then
            echo ""
            print_info "Please configure your domain's A record to point to: $SERVER_IP"
            print_info "After DNS propagation (5-30 minutes), retry this script to install the SSL certificate"
            echo ""
            exit 0
        fi
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
            print_message "✅ SSL certificate installed successfully!"
            
            # Enable auto-renewal
            if ! sudo systemctl is-enabled certbot.timer > /dev/null 2>&1; then
                sudo systemctl enable certbot.timer
                sudo systemctl start certbot.timer
                print_message "Auto-renewal enabled"
            fi
            
            # Test HTTPS
            echo ""
            print_message "Testing HTTPS connection..."
            sleep 2
            if curl -I https://$DOMAIN_NAME > /dev/null 2>&1; then
                print_message "✅ HTTPS is working correctly!"
                echo ""
                print_message "🌐 Your application is now available at: https://$DOMAIN_NAME"
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
    2)
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
        
        # Update Nginx configuration
        print_message "Updating Nginx configuration..."
        
        # Backup existing config
        sudo cp /etc/nginx/sites-available/myriade /etc/nginx/sites-available/myriade.backup
        
        # Create new SSL config
        sudo tee /etc/nginx/sites-available/myriade > /dev/null <<EOF
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME};
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN_NAME};

    # SSL Certificate
    ssl_certificate /etc/ssl/certs/${DOMAIN_NAME}.crt;
    ssl_certificate_key /etc/ssl/private/${DOMAIN_NAME}.key;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

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
        
        # Test configuration
        print_message "Testing Nginx configuration..."
        if sudo nginx -t; then
            print_message "Nginx configuration is valid"
            
            # Reload Nginx
            print_message "Reloading Nginx..."
            sudo systemctl reload nginx
            
            # Test HTTPS
            echo ""
            print_message "Testing HTTPS connection..."
            sleep 2
            if curl -Ik https://$DOMAIN_NAME > /dev/null 2>&1; then
                print_message "✅ HTTPS is working correctly!"
                echo ""
                print_message "🌐 Your application is now available at: https://$DOMAIN_NAME"
            else
                print_warning "HTTPS test failed. Please check:"
                echo "  1. Certificate files are valid"
                echo "  2. Certificate matches your domain"
                echo "  3. Nginx logs: sudo journalctl -u nginx -n 50"
            fi
        else
            print_error "Nginx configuration test failed"
            print_info "Restoring backup..."
            sudo mv /etc/nginx/sites-available/myriade.backup /etc/nginx/sites-available/myriade
            exit 1
        fi
        ;;
    3)
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
print_message "SSL certificate installation complete! 🎉"
echo ""

