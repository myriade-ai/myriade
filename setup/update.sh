#!/bin/bash

# Myriade Self-Hosted Update Script
# Self-update protocol: 1
# Usage: ./update.sh [version]
#
# Examples:
#   ./update.sh              # Update to latest version
#   ./update.sh 1.165.0      # Update to a specific version
#   ./update.sh versions     # List available versions

set -e

IMAGE="myriadeai/myriade"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
AUTOHEAL_SUSPENDED=0

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

# Fetch the maintained updater independently of the requested application
# version. HTTPS authenticates the public source; the checks below reject
# empty/error responses and syntax errors, not malicious code in that source.
# Use a subshell so cleanup traps do not replace the deployment's exit traps.
# Return 10 only when the caller must re-exec the newly installed script.
self_update() (
    local url="https://raw.githubusercontent.com/myriade-ai/myriade/master/setup/update.sh"
    local download="" backup=""
    trap 'rm -f -- "$download" "$backup"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM

    print_message "Checking for an updated deployment script..."
    download=$(mktemp "$SCRIPT_DIR/.update.sh.XXXXXX") || {
        print_error "Cannot write to $SCRIPT_DIR; run the updater with installation-owner permissions."
        return 1
    }
    if ! curl -fsSL --proto '=https' --proto-redir '=https' \
        --connect-timeout 10 --max-time 30 --retry 2 --retry-max-time 60 \
        "$url" -o "$download"; then
        print_error "Could not download the updater. The local script and services are unchanged."
        echo "To explicitly use the local script, rerun with MYRIADE_SKIP_SELF_UPDATE=1."
        return 1
    fi
    if [ "$(head -n 1 "$download")" != '#!/bin/bash' ] \
        || ! grep -qx '# Myriade Self-Hosted Update Script' "$download" \
        || ! grep -qx '# Self-update protocol: 1' "$download" \
        || ! bash -n "$download"; then
        print_error "Downloaded updater is invalid. The local script and services are unchanged."
        return 1
    fi
    if cmp -s "$SCRIPT_PATH" "$download"; then
        return 0
    fi

    # Both renames stay on the installation filesystem. Never truncate the
    # running script, and keep a recoverable copy before replacing it.
    backup="${download}.previous"
    if ! { cp -p "$SCRIPT_PATH" "$backup" \
        && chmod 755 "$download" \
        && mv -f "$backup" "${SCRIPT_PATH}.previous" \
        && mv -f "$download" "$SCRIPT_PATH"; }; then
        print_error "Could not install the updated script; no services have been changed."
        return 1
    fi
    print_message "Updater refreshed; previous copy saved to ${SCRIPT_PATH}.previous"
    return 10
)

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

# Never resume autoheal on failure or interruption: migrations may still be
# running, even after our readiness deadline has expired.
update_exit() {
    local status=$?
    if [ "$AUTOHEAL_SUSPENDED" -eq 1 ]; then
        print_warning "Autoheal remains stopped to protect any migration still running."
        echo "From the installation directory, inspect: sudo docker compose logs -f myriade"
        echo "Check Docker health: sudo docker compose ps myriade"
        echo "Once myriade is healthy, resume: sudo docker compose up -d --no-deps autoheal"
    fi
    return "$status"
}

# Wait for both HTTP readiness and Docker health. An HTTP success alone can
# precede the next Docker healthcheck; resuming autoheal then can restart an
# otherwise ready container still marked unhealthy.
wait_for_health() {
    local health_port="${1:-8080}"
    local timeout="${MYRIADE_UPDATE_TIMEOUT:-1800}"
    local deadline=$((SECONDS + timeout))
    local next_progress=$SECONDS
    local container_id state remaining probe_timeout delay
    container_id=$(docker compose ps --all -q myriade) || return 1
    if [ -z "$container_id" ]; then
        print_error "Myriade container was not created."
        return 1
    fi
    print_message "Waiting up to ${timeout}s for startup and database migrations..."
    while [ "$SECONDS" -lt "$deadline" ]; do
        state=$(docker inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container_id") || return 1
        case "$state" in
            exited\ *|dead\ *|restarting\ *)
                print_error "Myriade stopped or is restarting (${state}); check: sudo docker compose logs myriade"
                return 1
                ;;
        esac
        remaining=$((deadline - SECONDS))
        [ "$remaining" -gt 0 ] || break
        probe_timeout=5
        [ "$remaining" -ge "$probe_timeout" ] || probe_timeout=$remaining
        if { [ "$state" = "running healthy" ] || [ "$state" = "running none" ]; } \
            && curl -sf --connect-timeout "$probe_timeout" --max-time "$probe_timeout" \
                "http://localhost:${health_port}/health" > /dev/null 2>&1; then
            print_message "Application is healthy and responding on port ${health_port}"
            return 0
        fi
        if [ "$SECONDS" -ge "$next_progress" ]; then
            print_message "Still waiting (${state}); migrations may be in progress. Logs: sudo docker compose logs -f myriade"
            next_progress=$((SECONDS + 30))
        fi
        remaining=$((deadline - SECONDS))
        [ "$remaining" -gt 0 ] || break
        delay=2
        [ "$remaining" -ge "$delay" ] || delay=$remaining
        sleep "$delay"
    done
    print_error "Application did not become ready within ${timeout}s. The container has been left running; check: sudo docker compose logs -f myriade"
    return 1
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

    # Validate before pulling images or stopping services. Keep arithmetic
    # bounded and reject zero, negative values and malformed shell input.
    local timeout="${MYRIADE_UPDATE_TIMEOUT:-1800}"
    if ! [[ "$timeout" =~ ^[1-9][0-9]{0,4}$ ]] || [ "$timeout" -gt 86400 ]; then
        print_error "MYRIADE_UPDATE_TIMEOUT must be an integer between 1 and 86400 seconds."
        return 1
    fi

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

    if compose_has_service "" "autoheal"; then
        print_message "Stopping autoheal while startup migrations run..."
        trap update_exit EXIT
        trap 'exit 130' INT
        trap 'exit 143' TERM
        docker compose stop autoheal || return $?
        AUTOHEAL_SUSPENDED=1
    fi
    print_message "Restarting myriade..."
    docker compose up -d --no-build myriade || return $?

    # Do this before updating optional services: failures or slow pulls there
    # must not postpone readiness checks and resuming the app's supervisor.
    wait_for_health "$(get_health_port "$install_dir/.env")" || return $?
    if [ "$AUTOHEAL_SUSPENDED" -eq 1 ]; then
        print_message "Application is ready; starting autoheal..."
        docker compose up -d --no-build --no-deps autoheal || return $?
        AUTOHEAL_SUSPENDED=0
    fi

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

    wait "$cleanup_pid" || print_warning "Could not clean up old Docker images"

    echo ""
    print_message "Update complete!"
}

main() {
    # Listing versions is read-only. The skip flag also prevents a second
    # download after exec and supports explicitly managed/offline installations.
    if [ "${1:-}" != "versions" ] && [ "${MYRIADE_SKIP_SELF_UPDATE:-0}" != "1" ]; then
        local refresh_status=0
        self_update || refresh_status=$?
        case "$refresh_status" in
            0) ;;
            10) MYRIADE_SKIP_SELF_UPDATE=1 exec bash "$SCRIPT_PATH" "$@" ;;
            *) return "$refresh_status" ;;
        esac
    fi

    # Normalize version: add 'v' prefix if user provides a number without it
    local version="${1:-latest}"
    if [[ "$version" =~ ^[0-9]+\.[0-9]+ ]]; then
        version="v$version"
    fi

    case "$version" in
        versions) list_versions ;;
        *)
            check_version "$version"
            do_update "$version"
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
