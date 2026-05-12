#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_message() { echo -e "${GREEN}=====> $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error()   { echo -e "${RED}❌ $1${NC}"; }

print_banner() {
    local label="$1"
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    printf "║  %-62s║\n" "${label}"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# ---------------------------------------------------------------------------
# Port probing — bash builtin /dev/tcp avoids a hard dep on nc/lsof/ss.
# port_in_use returns 0 (true) if a TCP connect to 127.0.0.1:$port succeeds.
# ---------------------------------------------------------------------------
port_in_use() {
    local port="$1"
    (exec 3<>"/dev/tcp/127.0.0.1/${port}") 2>/dev/null
}

find_free_port() {
    local start="$1"
    local max_offset="${2:-50}"
    local offset port
    for offset in $(seq 0 "$max_offset"); do
        port=$((start + offset))
        if ! port_in_use "$port"; then
            echo "$port"
            return 0
        fi
    done
    return 1
}

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
WANT_SERVER=false
WANT_PUBLIC_IP=false
for _arg in "$@"; do
    case "$_arg" in
        --server)    WANT_SERVER=true ;;
        --public-ip) WANT_PUBLIC_IP=true ;;
    esac
done

# ---------------------------------------------------------------------------
# Platform & mode detection
#
# Modes:
#   desktop  → macOS, Windows (Git Bash/MSYS/Cygwin), WSL — Docker Desktop expected.
#              Installs into $HOME/.myriade, binds to 127.0.0.1, HOST=http://localhost:8080.
#   server   → Linux native (Ubuntu/Debian) — apt-installs Docker if missing.
#              Installs into /opt/myriade, binds to 0.0.0.0, HOST=http://<detected-ip>:8080.
# ---------------------------------------------------------------------------
OS_TYPE="$(uname -s)"
IS_WSL=false
if [ -r /proc/version ] && grep -qiE "(microsoft|wsl)" /proc/version 2>/dev/null; then
    IS_WSL=true
fi

case "$OS_TYPE" in
    Darwin*)
        OS_LABEL="macOS"
        MODE="desktop"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        OS_LABEL="Windows"
        MODE="desktop"
        ;;
    Linux*)
        if [ "$IS_WSL" = "true" ]; then
            OS_LABEL="WSL (Windows)"
            # WSL keeps its existing escape hatch: --server forces the apt path.
            if [ "$WANT_SERVER" = "true" ]; then
                MODE="server"
            else
                MODE="desktop"
            fi
        else
            OS_LABEL="Linux"
            MODE="server"
        fi
        ;;
    *)
        print_error "Unsupported operating system: $OS_TYPE"
        echo "Supported: macOS, Windows (Docker Desktop), WSL, Ubuntu 20.04+ / Debian 11+."
        exit 1
        ;;
esac

if [ "$WANT_SERVER" = "true" ] && [ "$MODE" = "desktop" ] && [ "$IS_WSL" != "true" ]; then
    print_warning "--server is Linux-only; ignoring on ${OS_LABEL}."
fi

print_banner "${OS_LABEL} detected — Myriade BI Quick Start (${MODE} mode)"

# ---------------------------------------------------------------------------
# Per-mode configuration
# ---------------------------------------------------------------------------
if [ "$MODE" = "desktop" ]; then
    INSTALL_DIR="${HOME}/.myriade"
    BIND_ADDRESS="127.0.0.1"
    DOCKER_COMPOSE=(docker compose)
    NEEDS_SUDO=false
else
    INSTALL_DIR="/opt/myriade"
    BIND_ADDRESS="0.0.0.0"
    DOCKER_COMPOSE=(sudo docker compose)
    NEEDS_SUDO=true
fi

DOWNLOAD_URL="${MYRIADE_DOWNLOAD_URL:-https://install.myriade.ai/myriade-bi-latest.tar.gz}"

# ---------------------------------------------------------------------------
# Docker bootstrap
# ---------------------------------------------------------------------------
ensure_docker_desktop() {
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed."
        echo ""
        echo "Install Docker Desktop, then re-run this script:"
        echo "  https://www.docker.com/products/docker-desktop"
        echo ""
        echo "Alternatives that also work: Colima, Rancher Desktop, OrbStack."
        exit 1
    fi
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is installed but the daemon is not running."
        echo "Start Docker Desktop (or your Docker runtime) and re-run this script."
        exit 1
    fi
    if ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose plugin not found."
        echo "Update Docker Desktop, or install the docker-compose-plugin package."
        exit 1
    fi
}

apt_install_docker() {
    print_message "Updating package index and installing prerequisites..."
    sudo apt update -y
    sudo apt install -y ca-certificates curl gnupg lsb-release unzip wget

    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        local os="$ID"
        local codename
        codename=$(lsb_release -cs)
    else
        print_error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi
    print_message "Detected OS: $os $codename"

    print_message "Removing old Docker installations if they exist..."
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    if [ ! -d /etc/apt/keyrings ]; then
        print_message "Adding Docker's official GPG key..."
        sudo install -m 0755 -d /etc/apt/keyrings
    fi

    if [ "$os" = "debian" ]; then
        curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $codename stable" | \
            sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    elif [ "$os" = "ubuntu" ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $codename stable" | \
            sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    else
        print_error "Unsupported OS: $os. Only Debian and Ubuntu are supported for the server install."
        exit 1
    fi
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    print_message "Updating package index with Docker repository..."
    sudo apt update -y

    print_message "Installing Docker..."
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    if [ "$EUID" -ne 0 ]; then
        print_message "Adding current user to the docker group..."
        sudo usermod -aG docker "$USER"
    fi

    print_message "Starting and enabling Docker service..."
    sudo systemctl start docker
    sudo systemctl enable docker

    if docker --version > /dev/null 2>&1; then
        print_message "Docker installed: $(docker --version)"
    else
        print_error "Docker installation failed"
        exit 1
    fi
}

if [ "$MODE" = "desktop" ]; then
    ensure_docker_desktop
else
    if ! command -v docker >/dev/null 2>&1 || ! sudo docker info >/dev/null 2>&1; then
        apt_install_docker
    fi
    if ! sudo docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose plugin not found after install."
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------
print_message "Preparing install directory: ${INSTALL_DIR}"
if [ "$NEEDS_SUDO" = "true" ]; then
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$(id -u):$(id -g)" "$INSTALL_DIR"
else
    mkdir -p "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ---------------------------------------------------------------------------
# Download release tarball (single source of truth for compose stack)
# ---------------------------------------------------------------------------
print_message "Downloading Myriade BI from $DOWNLOAD_URL..."
if ! curl -fsSL "$DOWNLOAD_URL" -o myriade.tar.gz; then
    print_error "Failed to download Myriade BI. Please check your internet connection."
    exit 1
fi

print_message "Extracting files..."
tar -xzf myriade.tar.gz --strip-components=1
rm myriade.tar.gz

if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found in release. Installation cannot continue."
    exit 1
fi

if [ -f "setup/install_certificate.sh" ]; then
    chmod +x setup/install_certificate.sh
fi
if [ -f "setup/update.sh" ]; then
    chmod +x setup/update.sh
fi

print_message "Myriade BI extracted to: $INSTALL_DIR"

# ---------------------------------------------------------------------------
# Architecture override: the myriadeai/myriade image is published amd64-only.
# On ARM hosts (Apple Silicon, ARM Linux) compose would fail to pull the native
# manifest. Drop a compose override that pins ONLY the myriade service to
# linux/amd64 — Postgres stays native.
#
# IMPORTANT: docker-compose.override.yml is MYRIADE-managed (carries the bwrap
# sandbox security_opt block, replaced on every setup/update.sh run). We must
# NOT write to it. Instead we write a sibling file and chain it via the
# COMPOSE_FILE env var so Compose merges all three layers:
#   docker-compose.yml + docker-compose.override.yml + docker-compose.platform.yml
# ---------------------------------------------------------------------------
ARCH="$(uname -m)"
PLATFORM_OVERRIDE_FILE=""
case "$ARCH" in
    arm64|aarch64)
        cat > docker-compose.platform.yml <<'YML'
# Auto-generated by setup/install.sh on ARM hosts. The myriadeai/myriade
# image is published amd64-only, so compose would fail to pull the native
# manifest on Apple Silicon / ARM Linux. Pinning the myriade service here
# (Postgres stays native) keeps the host-side override file untouched and
# lets COMPOSE_FILE chain this cleanly with docker-compose.override.yml.
services:
  myriade:
    platform: linux/amd64
YML
        PLATFORM_OVERRIDE_FILE="docker-compose.platform.yml"
        print_message "Detected ${ARCH} — pinning myriade service to linux/amd64 via ${PLATFORM_OVERRIDE_FILE}."
        ;;
esac

# ---------------------------------------------------------------------------
# Preserve existing .env values BEFORE deciding port / HOST so re-runs are
# stable (CREDENTIAL_ENCRYPTION_KEY especially — losing it makes encrypted
# warehouse credentials unrecoverable).
# ---------------------------------------------------------------------------
print_message "Configuring environment variables..."
if [ -f ".env" ]; then
    print_warning "Existing .env file found. Preserving existing configuration."
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

# ---------------------------------------------------------------------------
# HTTP port
#   server  → always 8080 (firewall rules, install_certificate.sh, docs all
#             assume it).
#   desktop → trust persisted MYRIADE_HTTP_PORT if present; otherwise scan
#             8080..8130 for the first free one. Avoids "port already
#             allocated" failures on machines running other dev stacks.
# ---------------------------------------------------------------------------
if [ "$MODE" = "server" ]; then
    HTTP_PORT=8080
else
    if [ -n "${MYRIADE_HTTP_PORT:-}" ]; then
        HTTP_PORT="$MYRIADE_HTTP_PORT"
    else
        HTTP_PORT=$(find_free_port 8080 50) || {
            print_error "Could not find a free TCP port in 8080..8130."
            echo "Free up port 8080 (or any in that range) and re-run."
            exit 1
        }
        if [ "$HTTP_PORT" != "8080" ]; then
            print_warning "Port 8080 is in use; using ${HTTP_PORT} instead."
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Resolve HOST default (only used if .env doesn't already define HOST)
# ---------------------------------------------------------------------------
if [ "$MODE" = "server" ]; then
    if [ "$WANT_PUBLIC_IP" = "true" ]; then
        SERVER_IP=$(curl -s --connect-timeout 5 ifconfig.me || curl -s --connect-timeout 5 icanhazip.com || hostname -I 2>/dev/null | awk '{print $1}')
        print_message "Using public IP: ${SERVER_IP}"
    else
        SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
        print_message "Using private IP: ${SERVER_IP}"
    fi
    DEFAULT_HOST="http://${SERVER_IP}:${HTTP_PORT}"
else
    DEFAULT_HOST="http://localhost:${HTTP_PORT}"
fi

# ---------------------------------------------------------------------------
# Adjust compose port mapping. Combines server bind-address change with the
# desktop auto-picked port. sed -i.bak for BSD/GNU portability.
# ---------------------------------------------------------------------------
TARGET_BINDING="${BIND_ADDRESS}:${HTTP_PORT}:8080"
if [ "$TARGET_BINDING" != "127.0.0.1:8080:8080" ]; then
    print_message "Configuring myriade port mapping: ${TARGET_BINDING}"
    sed -i.bak "s|127.0.0.1:8080:8080|${TARGET_BINDING}|g" docker-compose.yml
    rm -f docker-compose.yml.bak
fi

# ---------------------------------------------------------------------------
# Strip the db service's host port mapping in desktop mode. The shipped
# compose exposes Postgres on 127.0.0.1:2345 for "local debugging only" —
# desktop quickstart users never need this and it's a frequent source of
# port conflicts when other Postgres instances are running locally.
# ---------------------------------------------------------------------------
if [ "$MODE" = "desktop" ]; then
    awk '
        BEGIN          { in_db = 0; skipping = 0 }
        /^  db:$/      { in_db = 1; print; next }
        /^  [a-z]/ && !/^    / { in_db = 0; skipping = 0 }
        in_db && /^    ports:/ { skipping = 1; next }
        skipping && /^      / { next }
        skipping       { skipping = 0 }
                       { print }
    ' docker-compose.yml > docker-compose.yml.tmp \
        && mv docker-compose.yml.tmp docker-compose.yml
fi

# ---------------------------------------------------------------------------
# Generate any missing secrets and write .env
# ---------------------------------------------------------------------------
if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    print_message "Generated secure database password"
fi

if [ -z "${CREDENTIAL_ENCRYPTION_KEY:-}" ]; then
    # Fernet keys: 32 bytes, URL-safe base64.
    CREDENTIAL_ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n' | tr '+/' '-_')
    print_message "Generated credential encryption key"
fi

# Setting COMPOSE_FILE disables Compose's implicit override.yml auto-load,
# so we must enumerate it — but only when it's on disk. On a fresh install
# the override is absent (synced from the image later by update.sh); listing
# it unconditionally makes `docker compose pull` fail with ENOENT.
COMPOSE_FILE_LINE=""
if [ -n "$PLATFORM_OVERRIDE_FILE" ]; then
    compose_files="docker-compose.yml"
    if [ -f "docker-compose.override.yml" ]; then
        compose_files="${compose_files}:docker-compose.override.yml"
    fi
    compose_files="${compose_files}:${PLATFORM_OVERRIDE_FILE}"
    COMPOSE_FILE_LINE="COMPOSE_FILE=${compose_files}"
    # Earlier `set -a; . ./.env` may have exported a stale COMPOSE_FILE (e.g.
    # one listing docker-compose.override.yml from a previous failed run).
    # Compose gives the shell env precedence over `.env`, so overwrite it
    # with the freshly computed list before invoking compose below.
    export COMPOSE_FILE="$compose_files"
else
    # Same reason: clear any stale value sourced from `.env` so Compose
    # falls back to its implicit yml + override.yml auto-load.
    unset COMPOSE_FILE
fi

cat > .env << EOF
COMPOSE_PROJECT_NAME=myriade
POSTGRES_DB=${POSTGRES_DB:-myriade}
POSTGRES_USER=${POSTGRES_USER:-myriade}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
HOST=${HOST:-${DEFAULT_HOST}}
CREDENTIAL_ENCRYPTION_KEY=${CREDENTIAL_ENCRYPTION_KEY}
MYRIADE_HTTP_PORT=${HTTP_PORT}
${COMPOSE_FILE_LINE}
EOF
chmod 600 .env
print_message "Environment configuration saved to .env"

# ---------------------------------------------------------------------------
# Pull & start
# ---------------------------------------------------------------------------
print_message "Pulling images..."
"${DOCKER_COMPOSE[@]}" pull

print_message "Starting Myriade BI with Docker Compose..."
if "${DOCKER_COMPOSE[@]}" up -d; then
    print_message "Containers started"
else
    print_error "Failed to start Docker containers"
    exit 1
fi

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
print_message "Waiting for application to be ready..."
MAX_ATTEMPTS=60
ATTEMPT=0
HEALTHY=false
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -sf "http://localhost:${HTTP_PORT}/health" > /dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    sleep 2
done

echo ""
if [ "$HEALTHY" = "true" ]; then
    print_banner "✅ Myriade BI is running"
else
    print_warning "Application did not respond on /health within 2 minutes."
    echo "Inspect logs with: ${DOCKER_COMPOSE[*]} -f ${INSTALL_DIR}/docker-compose.yml logs -f myriade"
fi

# ---------------------------------------------------------------------------
# Final message
# ---------------------------------------------------------------------------
ACCESS_URL="${HOST:-${DEFAULT_HOST}}"
print_message "🌐 Open ${ACCESS_URL} in your browser."
echo ""
echo "Useful commands:"
echo "  ${DOCKER_COMPOSE[*]} -f ${INSTALL_DIR}/docker-compose.yml logs -f myriade"
echo "  ${DOCKER_COMPOSE[*]} -f ${INSTALL_DIR}/docker-compose.yml restart"
echo "  ${DOCKER_COMPOSE[*]} -f ${INSTALL_DIR}/docker-compose.yml down       # stop"
echo "  ${DOCKER_COMPOSE[*]} -f ${INSTALL_DIR}/docker-compose.yml up -d      # start"
echo ""

if [ "$MODE" = "server" ]; then
    print_warning "If users access Myriade via a different IP or domain, update HOST in ${INSTALL_DIR}/.env and restart."
    echo ""
    print_message "Tip: re-run with --public-ip to use the server's public IP."
    echo ""
    print_message "To add a domain and SSL certificate, run:"
    echo "  sudo ${INSTALL_DIR}/setup/install_certificate.sh YOUR_DOMAIN.com"
    echo ""
fi

print_warning "Back up ${INSTALL_DIR}/.env — it holds the key that decrypts your warehouse credentials."
echo ""

print_message "Running containers:"
"${DOCKER_COMPOSE[@]}" ps

echo ""
print_message "Installation complete! 🎉"
