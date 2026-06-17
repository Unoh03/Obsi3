#!/bin/bash
set -euo pipefail

# Single NFS server setup.
#
# Usage:
#   sudo EXPORT_NET="CLIENT_CIDR" bash nfs-server.sh
#
# Optional:
#   SHARE_DIR=/share_directory
#   EXPORT_OPTIONS=rw,sync,no_subtree_check,no_root_squash
#   OPEN_UFW=1

SHARE_DIR="${SHARE_DIR:-/share_directory}"
EXPORT_NET="${EXPORT_NET:-}"
EXPORT_OPTIONS="${EXPORT_OPTIONS:-rw,sync,no_subtree_check}"
OPEN_UFW="${OPEN_UFW:-1}"

log() {
    echo "[INFO] $*"
}

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "Run as root. Example: sudo EXPORT_NET='CLIENT_CIDR' bash nfs-server.sh"
    fi
}

main() {
    require_root
    [ -n "$EXPORT_NET" ] || die "Set EXPORT_NET. Example: EXPORT_NET='CLIENT_CIDR'"

    log "Installing NFS server package."
    apt update
    apt install -y nfs-kernel-server

    log "Preparing share directory: ${SHARE_DIR}"
    mkdir -p "$SHARE_DIR"
    chown nobody:nogroup "$SHARE_DIR"
    chmod 777 "$SHARE_DIR"

    log "Registering export for ${EXPORT_NET}."
    sed -i "\|^${SHARE_DIR}[[:space:]]|d" /etc/exports
    echo "${SHARE_DIR} ${EXPORT_NET}(${EXPORT_OPTIONS})" >> /etc/exports

    exportfs -ra
    systemctl enable nfs-kernel-server
    systemctl restart nfs-kernel-server

    if command -v ufw >/dev/null 2>&1 && [ "$OPEN_UFW" = "1" ]; then
        ufw allow from "$EXPORT_NET" to any port 2049 proto tcp comment 'NFS from project network' || true
    fi

    log "NFS server setup completed."
    echo "[INFO] Export: ${SHARE_DIR} ${EXPORT_NET}(${EXPORT_OPTIONS})"
    echo "[INFO] Check: showmount -e 127.0.0.1"
}

main "$@"
