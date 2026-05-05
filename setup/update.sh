#!/bin/bash

# Myriade Self-Hosted Update Script
# Usage: ./update.sh [version]
#
# Examples:
#   ./update.sh              # Update to latest version
#   ./update.sh 1.165.0      # Update to a specific version
#   ./update.sh versions     # List available versions

set -e

IMAGE="myriadeai/myriade"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_message() {
    echo -e "${GREEN}=====> $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Find the Myriade install directory (where docker-compose.yml lives)
find_install_dir() {
    # Prefer the directory containing this script (setup/ lives inside the install dir)
    local script_parent
    script_parent="$(cd "$SCRIPT_DIR/.." && pwd)"
    if [ -f "$script_parent/docker-compose.yml" ]; then
        echo "$script_parent"
        return
    fi
    # Current working directory
    if [ -f "./docker-compose.yml" ]; then
        echo "."
        return
    fi
    # Default install locations
    if [ -f "/opt/myriade/docker-compose.yml" ]; then
        echo "/opt/myriade"
        return
    fi
    if [ -f "/opt/myriade-bi/docker-compose.yml" ]; then
        echo "/opt/myriade-bi"
        return
    fi
    print_error "Could not find docker-compose.yml"
    echo "Run this script from your Myriade installation directory."
    exit 1
}

# List available versions from Docker Hub
list_versions() {
    echo "📦 Available versions for $IMAGE:"
    echo ""
    curl -s "https://hub.docker.com/v2/repositories/${IMAGE}/tags?page_size=20&ordering=last_updated" \
        | grep -o '"name":"[^"]*"' \
        | sed 's/"name":"//;s/"//' \
        | head -20
    echo ""
    echo "Showing latest 20 versions. See all at: https://hub.docker.com/r/${IMAGE}/tags"
}

# Check if a version exists in Docker Hub
check_version() {
    local version="$1"
    if [ "$version" = "latest" ]; then
        return 0
    fi
    print_message "Checking if version $version exists..."
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://hub.docker.com/v2/repositories/${IMAGE}/tags/${version}")
    if [ "$status" != "200" ]; then
        print_error "Version '$version' not found on Docker Hub"
        echo ""
        echo "Run './update.sh versions' to see available versions"
        exit 1
    fi
    print_message "Version $version found"
}

# Wait for health check
wait_for_health() {
    print_message "Waiting for application to be ready..."
    local max_attempts=60
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
            print_message "Application is healthy and responding on port 8080"
            return 0
        fi
        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            print_warning "Application may not be ready yet. Check logs with: sudo docker compose logs myriade"
            return 1
        fi
        sleep 2
    done
}

# Sync host-side bwrap sandbox config from the just-pulled image. Two files
# need to land on the host filesystem:
#   - docker/seccomp/dbt-sandbox.json: the seccomp profile referenced by the
#     security_opt: seccomp=... entry
#   - docker-compose.override.yml: the security_opt block itself, auto-loaded
#     by Docker Compose so the customer's main docker-compose.yml stays
#     untouched
# Both are bundled inside the image starting v1.186+; older images that don't
# carry them silently skip this step (the Python `should_sandbox_dbt()` probe
# falls back to running dbt unsandboxed in that case).
sync_sandbox_config() {
    local install_dir="$1"
    local version="${MYRIADE_VERSION:-latest}"
    local image="${IMAGE}:${version}"

    mkdir -p "$install_dir/docker/seccomp"

    # Create a *fresh* stopped container directly from the image (NOT
    # `docker compose create`, which is a no-op when the service is already
    # running and would point us at the live production container — we'd
    # then `docker rm -f` it at the end of this function and cause an
    # outage). `docker create` always returns a brand-new container ID we
    # know is safe to remove.
    local cid
    cid=$(docker create "$image" 2>/dev/null) || cid=""
    if [ -z "$cid" ]; then
        print_warning "Could not create a temporary container from $image; skipping sandbox config sync"
        return 0
    fi

    local synced_anything=0

    if docker cp "${cid}:/app/docker/seccomp/dbt-sandbox.json" \
                 "$install_dir/docker/seccomp/dbt-sandbox.json" 2>/dev/null; then
        print_message "Synced bwrap seccomp profile"
        synced_anything=1
    fi

    # The override file is what actually activates the sandbox - install it
    # only if the customer doesn't already have a custom override (which
    # would be unusual for a self-hosted prod setup, but handle it safely).
    local override_dest="$install_dir/docker-compose.override.yml"
    if [ -f "$override_dest" ] && ! grep -q "dbt-sandbox.json" "$override_dest"; then
        print_warning "An existing docker-compose.override.yml was found that does not match"
        print_warning "the Myriade-shipped sandbox override. Leaving it alone to avoid"
        print_warning "clobbering local customizations. The bwrap sandbox will not be active"
        print_warning "until you merge the security_opt block from /app/docker-compose.override.yml"
        print_warning "in the image into your override."
    else
        if docker cp "${cid}:/app/docker-compose.override.yml" "$override_dest" 2>/dev/null; then
            print_message "Synced docker-compose.override.yml (activates the bwrap sandbox)"
            synced_anything=1
        fi
    fi

    if [ "$synced_anything" -eq 0 ]; then
        print_warning "Image does not bundle the sandbox config yet; skipping (older version)"
    fi

    # Tear down the throwaway container we created above. This is safe
    # because $cid was produced by `docker create <image>` (a fresh
    # container), never by `docker compose ps -q myriade` (which would
    # have pointed at the live production container).
    docker rm -f "$cid" >/dev/null 2>&1 || true
}

# Main update logic
do_update() {
    local version="$1"
    local install_dir
    install_dir=$(find_install_dir)

    cd "$install_dir"

    # Get current version before update
    local current_version
    current_version=$(docker compose exec myriade cat VERSION 2>/dev/null | head -1 || echo "unknown")
    print_message "Current version: $current_version"
    print_message "Updating to: $version"

    export MYRIADE_VERSION="$version"

    print_message "Pulling new image..."
    docker compose pull myriade

    print_message "Syncing host-side sandbox config from image..."
    sync_sandbox_config "$install_dir"

    print_message "Restarting myriade..."
    docker compose up -d myriade

    # Restart logging if active
    docker compose --profile logging up -d 2>/dev/null || true

    print_message "Cleaning up old images..."
    docker image prune -af --filter 'until=24h' > /dev/null

    wait_for_health

    echo ""
    print_message "Update complete!"
}

# Normalize version: add 'v' prefix if user provides a number without it
VERSION="${1:-latest}"
if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+ ]]; then
    VERSION="v$VERSION"
fi

case "$VERSION" in
    versions)
        list_versions
        ;;
    *)
        check_version "$VERSION"
        do_update "$VERSION"
        ;;
esac
