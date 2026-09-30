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
    local health_port="${1:-8080}"
    print_message "Waiting for application to be ready..."
    local max_attempts=60
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "http://localhost:${health_port}/health" > /dev/null 2>&1; then
            print_message "Application is healthy and responding on port ${health_port}"
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

env_file_has_value() {
    local env_file="$1"
    local variable="$2"
    [ -f "$env_file" ] && grep -qE "^${variable}=.+" "$env_file"
}

compose_has_service() {
    local profile="$1"
    local service="$2"
    if [ -n "$profile" ]; then
        docker compose --profile "$profile" config --services 2>/dev/null | grep -qx "$service"
    else
        docker compose config --services 2>/dev/null | grep -qx "$service"
    fi
}

get_health_port() {
    local env_file="$1"
    local port="${MYRIADE_HTTP_PORT:-}"
    if [ -z "$port" ] && [ -f "$env_file" ]; then
        port=$(sed -n 's/^MYRIADE_HTTP_PORT=//p' "$env_file" | head -1)
    fi
    case "$port" in
        ''|*[!0-9]*) echo "8080" ;;
        *) echo "$port" ;;
    esac
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
            # Setting COMPOSE_FILE disables Compose's implicit override.yml
            # auto-load, so when .env enumerates the merge list (ARM hosts)
            # we must splice the override in by hand.
            local env_file="$install_dir/.env"
            if [ -f "$env_file" ] \
                && grep -q '^COMPOSE_FILE=' "$env_file" \
                && ! grep -q '^COMPOSE_FILE=.*docker-compose\.override\.yml' "$env_file"; then
                sed -i.bak \
                    's|^COMPOSE_FILE=docker-compose\.yml|COMPOSE_FILE=docker-compose.yml:docker-compose.override.yml|' \
                    "$env_file"
                rm -f "${env_file}.bak"
                print_message "Updated .env COMPOSE_FILE to include docker-compose.override.yml"
            fi
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

# Raise the nginx upload cap to match the backend's 100 MB per-file limit
# (service/domains/conversation/files_api.py). nginx only exists on installs
# that ran install_certificate.sh; it is installed once and never re-templated,
# so without this step existing customers keep the old 10M cap and every
# attachment over that size fails with a bare 413. Only the one directive is
# rewritten - the rest of the file (domain, certificates, local tweaks) is
# left untouched, and nginx -t guards the reload.
NGINX_SITE="/etc/nginx/sites-available/myriade"
NGINX_MAX_BODY="100M"

sync_nginx_config() {
    [ -f "$NGINX_SITE" ] || return 0
    if grep -qE "client_max_body_size ${NGINX_MAX_BODY};" "$NGINX_SITE"; then
        return 0
    fi
    if ! grep -qE "client_max_body_size [0-9]+[kKmMgG]?;" "$NGINX_SITE"; then
        return 0
    fi
    print_message "Raising nginx client_max_body_size to ${NGINX_MAX_BODY}..."
    if ! sudo sed -i -E "s/client_max_body_size [0-9]+[kKmMgG]?;/client_max_body_size ${NGINX_MAX_BODY};/" "$NGINX_SITE"; then
        print_warning "Could not edit $NGINX_SITE; file uploads stay capped at the current nginx limit"
        return 0
    fi
    if sudo nginx -t >/dev/null 2>&1 && sudo systemctl reload nginx; then
        print_message "nginx reloaded"
    else
        print_warning "nginx config test or reload failed; run 'sudo nginx -t' and 'sudo systemctl reload nginx' manually"
    fi
}

# Main update logic
do_update() {
    local version="$1"
    local install_dir
    install_dir=$(find_install_dir)

    cd "$install_dir"

    local sandbox_enabled=0
    if [ -n "${SANDBOX_TOKEN:-}" ] || env_file_has_value "$install_dir/.env" "SANDBOX_TOKEN"; then
        sandbox_enabled=1
    fi

    # Remember whether logging was already running. A profile flag enables a
    # service; it does not merely select an existing one.
    local logging_was_running=0
    if docker compose --profile logging ps -q vector 2>/dev/null | grep -q .; then
        logging_was_running=1
    fi

    # Get current version before update
    local current_version
    current_version=$(docker compose exec myriade cat VERSION 2>/dev/null | head -1 || echo "unknown")
    print_message "Current version: $current_version"
    print_message "Updating to: $version"

    export MYRIADE_VERSION="$version"

    # Existing installs already know about the sandbox service, so pull both
    # independent images concurrently. Fresh/older installs first need the
    # override extracted from the app image and use the serial fallback below.
    local app_pull_pid
    local sandbox_pull_pid=""
    if [ "$sandbox_enabled" -eq 1 ] && compose_has_service "code-execution" "sandbox"; then
        print_message "Pulling app and sandbox images in parallel..."
        docker compose pull myriade &
        app_pull_pid=$!
        docker compose --profile code-execution pull sandbox &
        sandbox_pull_pid=$!
        if ! wait "$app_pull_pid"; then
            wait "$sandbox_pull_pid" 2>/dev/null || true
            print_error "Could not pull the Myriade image"
            return 1
        fi
    else
        print_message "Pulling new image..."
        docker compose pull myriade
    fi

    print_message "Syncing host-side sandbox config from image..."
    sync_sandbox_config "$install_dir"

    sync_nginx_config

    print_message "Restarting myriade..."
    local app_services=(myriade)
    if compose_has_service "" "autoheal"; then
        app_services+=(autoheal)
    fi
    docker compose up -d --no-build "${app_services[@]}"

    if [ "$logging_was_running" -eq 1 ]; then
        print_message "Restarting logging..."
        docker compose --profile logging up -d --no-build vector \
            || print_warning "Could not restart logging; check: docker compose --profile logging logs vector"
    fi

    # Update the code-execution sandbox only when the operator has opted in
    # by setting SANDBOX_TOKEN in their .env. The sandbox service is
    # profile-gated and lives in docker-compose.override.yml, so it is never
    # touched by `pull myriade` / `up -d myriade` above. The explicit pull
    # matters: `up -d` alone reuses whatever local image exists, so without
    # it the runner stays on the image it was first started with forever
    # (e.g. a runner missing duckdb/pyarrow while the app already sends
    # Parquet seeds). Failures are non-fatal (the app update already
    # succeeded) but must be visible, not swallowed.
    if [ "$sandbox_enabled" -eq 1 ]; then
        print_message "Updating code-execution sandbox..."
        if [ -n "$sandbox_pull_pid" ]; then
            wait "$sandbox_pull_pid" \
                || print_warning "Could not pull the sandbox image; the runner keeps its current (possibly outdated) image"
        else
            docker compose --profile code-execution pull sandbox \
                || print_warning "Could not pull the sandbox image; the runner keeps its current (possibly outdated) image"
        fi
        docker compose --profile code-execution up -d --no-build sandbox \
            || print_warning "Could not restart the sandbox; check: docker compose --profile code-execution logs sandbox"
    fi

    print_message "Cleaning up old dangling images..."
    docker image prune -f --filter 'until=24h' > /dev/null &
    local cleanup_pid=$!

    local health_status=0
    wait_for_health "$(get_health_port "$install_dir/.env")" || health_status=$?
    wait "$cleanup_pid" || print_warning "Could not clean up old Docker images"
    if [ "$health_status" -ne 0 ]; then
        return "$health_status"
    fi

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
