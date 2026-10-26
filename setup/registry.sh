#!/bin/bash
# Sourced by install.sh, update.sh and deploy.sh: where Myriade images live,
# how a host logs in to pull them, and how a pulled image is checked against
# the key CI signs every release with.
#
# Images are private. A host pulls them with, in this order:
#   1. registry-key.json next to docker-compose.yml — the read-only key
#      Myriade issues to each self-hosted customer;
#   2. the VM's own service account, on a Google Compute Engine VM;
#   3. whatever `docker login` the operator already made (e.g. a pull
#      secret managed by the customer's own tooling).
#
# Callers set DOCKER (array) to the docker command to run, e.g. (sudo docker).

MYRIADE_REGISTRY="europe-docker.pkg.dev"
MYRIADE_REPOSITORY="ada-intelligence-436410/myriade"
MYRIADE_IMAGE="${MYRIADE_REGISTRY}/${MYRIADE_REPOSITORY}/myriade"
MYRIADE_SANDBOX_IMAGE="${MYRIADE_REGISTRY}/${MYRIADE_REPOSITORY}/sandbox"
MYRIADE_REGISTRY_KEY_FILE="registry-key.json"

# Public half of the Cloud KMS key the release workflow signs images with
# (.github/workflows/build.yml). Pinned here rather than read from the image:
# a key shipped inside the image would vouch for whatever image carries it.
MYRIADE_COSIGN_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAERRvMF44a5yEfy5qy+Aws97EyhEa3
bRdeLF9KapYQ4G157fvknPNGcz9TJ6o32VZPyePr63gq6jZF4ooQo4kpGw==
-----END PUBLIC KEY-----'

COSIGN_VERSION="v2.6.5"

if [ -z "${DOCKER+x}" ]; then
    DOCKER=(docker)
fi

# Sets REGISTRY_USER / REGISTRY_PASSWORD; returns 1 when neither a key file
# nor a GCE service account is available.
registry_credentials() {
    local install_dir="$1"
    local key_file="$install_dir/$MYRIADE_REGISTRY_KEY_FILE"
    if [ -f "$key_file" ]; then
        REGISTRY_USER="_json_key"
        REGISTRY_PASSWORD="$(cat "$key_file")"
        return 0
    fi
    local token
    token=$(curl -sf -m 2 -H "Metadata-Flavor: Google" \
        "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \
        | sed -n 's/.*"access_token" *: *"\([^"]*\)".*/\1/p') || token=""
    if [ -n "$token" ]; then
        REGISTRY_USER="oauth2accesstoken"
        REGISTRY_PASSWORD="$token"
        return 0
    fi
    return 1
}

registry_login() {
    local install_dir="$1"
    if ! registry_credentials "$install_dir"; then
        echo "No $MYRIADE_REGISTRY_KEY_FILE in $install_dir and not on a GCE VM: relying on an existing docker login to $MYRIADE_REGISTRY" >&2
        return 0
    fi
    printf '%s' "$REGISTRY_PASSWORD" \
        | "${DOCKER[@]}" login -u "$REGISTRY_USER" --password-stdin "https://$MYRIADE_REGISTRY" >/dev/null
}

_registry_api() {
    local install_dir="$1"
    local path="$2"
    shift 2
    registry_credentials "$install_dir" || return 2
    local auth
    auth=$(printf '%s:%s' "$REGISTRY_USER" "$REGISTRY_PASSWORD" | base64 | tr -d '\n')
    curl -sf -H "Authorization: Basic $auth" "$@" "https://$MYRIADE_REGISTRY/v2/$MYRIADE_REPOSITORY/$path"
}

# Release tags of the app image, newest last.
registry_versions() {
    _registry_api "$1" "myriade/tags/list" \
        | grep -o '"tags" *: *\[[^]]*\]' \
        | sed 's/.*\[//; s/\]//' \
        | tr ',' '\n' \
        | tr -d '" ' \
        | grep -E '^v?[0-9]+\.[0-9]+' \
        | sort -V
}

# Returns 0 if the tag exists, 1 if it does not, 2 if it cannot be checked.
registry_has_version() {
    local status=0
    _registry_api "$1" "myriade/manifests/$2" -o /dev/null -I \
        -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json" \
        || status=$?
    case "$status" in
        0) return 0 ;;
        2) return 2 ;;
        *) return 1 ;;
    esac
}

# Prints the path of a cosign binary, installing the pinned release under
# $install_dir/.bin when none is on PATH.
ensure_cosign() {
    local install_dir="$1"
    if command -v cosign >/dev/null 2>&1; then
        command -v cosign
        return 0
    fi
    local ext=""
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) ext=".exe" ;;
    esac
    local bin="$install_dir/.bin/cosign$ext"
    if [ -x "$bin" ]; then
        echo "$bin"
        return 0
    fi
    local os arch sha
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    if [ -n "$ext" ]; then
        os="windows"
    fi
    case "$(uname -m)" in
        x86_64|amd64) arch="amd64" ;;
        arm64|aarch64) arch="arm64" ;;
        *) echo "Unsupported architecture for cosign: $(uname -m)" >&2; return 1 ;;
    esac
    case "$os-$arch" in
        linux-amd64)  sha="c3b4f5410e608af03a5eb0aaac84a4313d8da131248e08ff1759ac70c79d1644" ;;
        linux-arm64)  sha="426193b4c5da4d4d643e822f48fe0cc8a476ca1782a272704831f5a0cef716d7" ;;
        darwin-amd64) sha="0f8a1a70c81de9740a2b62e91307ff396ce54e7dd80568d42411bb2d9d44269c" ;;
        darwin-arm64) sha="4d41cc18f0563907c0c785b51db76e1d1af10db4422b605ba876b1758e1771ab" ;;
        windows-amd64) sha="19ec346d0050f59ffad9694da97ef9704be34ec60ddc41c5f1d16d8619385825" ;;
        *) echo "Unsupported platform for cosign: $os-$arch" >&2; return 1 ;;
    esac
    mkdir -p "$install_dir/.bin"
    local tmp="$bin.download"
    if ! curl -fsSL -o "$tmp" \
        "https://github.com/sigstore/cosign/releases/download/${COSIGN_VERSION}/cosign-${os}-${arch}${ext}"; then
        echo "Could not download cosign ${COSIGN_VERSION}" >&2
        rm -f "$tmp"
        return 1
    fi
    local actual
    actual=$( (sha256sum "$tmp" 2>/dev/null || shasum -a 256 "$tmp") | cut -d' ' -f1)
    if [ "$actual" != "$sha" ]; then
        echo "cosign checksum mismatch (expected $sha, got $actual)" >&2
        rm -f "$tmp"
        return 1
    fi
    chmod +x "$tmp"
    mv "$tmp" "$bin"
    echo "$bin"
}

# Verifies the exact digest a local image tag was pulled as, so what runs is
# what was checked. MYRIADE_SKIP_SIGNATURE_CHECK=1 skips it (images released
# before signing began carry no signature).
verify_image() {
    local install_dir="$1"
    local image_ref="$2"
    if [ "${MYRIADE_SKIP_SIGNATURE_CHECK:-0}" = "1" ]; then
        echo "MYRIADE_SKIP_SIGNATURE_CHECK=1: NOT verifying the signature of $image_ref" >&2
        return 0
    fi
    local repo="${image_ref%:*}"
    local digest_ref
    digest_ref=$("${DOCKER[@]}" image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$image_ref" 2>/dev/null \
        | grep -m1 "^${repo}@sha256:") || digest_ref=""
    if [ -z "$digest_ref" ]; then
        echo "Cannot find the registry digest of $image_ref" >&2
        return 1
    fi
    local cosign
    cosign=$(ensure_cosign "$install_dir") || return 1
    local key_file
    key_file=$(mktemp)
    printf '%s\n' "$MYRIADE_COSIGN_PUBLIC_KEY" > "$key_file"
    # Same user as docker, so cosign reads the credentials registry_login stored.
    local run_as=()
    if [ "${DOCKER[0]}" = "sudo" ]; then
        run_as=(sudo)
    fi
    local status=0
    "${run_as[@]}" "$cosign" verify --key "$key_file" --insecure-ignore-tlog=true "$digest_ref" >/dev/null 2>&1 || status=$?
    rm -f "$key_file"
    if [ "$status" -ne 0 ]; then
        echo "Signature verification FAILED for $digest_ref" >&2
        return 1
    fi
    echo "Signature verified: $digest_ref" >&2
}
