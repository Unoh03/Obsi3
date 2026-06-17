#!/bin/bash
set -euo pipefail

# Update backend list for the single nginx load balancer.
#
# Usage:
#   sudo BACKENDS="WEB1_IP WEB2_IP" bash lb-upstream-update.sh
#   sudo bash lb-upstream-update.sh WEB1_IP WEB2_IP

LISTEN_PORT="${LISTEN_PORT:-80}"
BACKEND_PORT="${BACKEND_PORT:-80}"
CONF_FILE="${CONF_FILE:-/etc/nginx/conf.d/project-load-balancer.conf}"
BACKENDS="${BACKENDS:-${*:-}}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/project-lb}"

log() {
    echo "[INFO] $*"
}

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "Run as root."
    fi
}

normalize_backend() {
    local backend="$1"

    case "$backend" in
        *:*)
            printf '%s' "$backend"
            ;;
        *)
            printf '%s:%s' "$backend" "$BACKEND_PORT"
            ;;
    esac
}

backup_config() {
    if [ -f "$CONF_FILE" ]; then
        mkdir -p "$BACKUP_DIR"
        cp -a "$CONF_FILE" "${BACKUP_DIR}/$(basename "$CONF_FILE").$(date +%Y%m%d-%H%M%S).bak"
    fi
}

write_nginx_config() {
    local upstream=""
    local backend

    for backend in $BACKENDS; do
        backend="$(normalize_backend "$backend")"
        upstream="${upstream}    server ${backend};\n"
    done

    [ -n "$upstream" ] || die "No backend provided."

    printf '%b' "upstream backend_nodes {\n${upstream}}\n\nserver {\n    listen ${LISTEN_PORT};\n    server_name _;\n\n    location / {\n        proxy_pass http://backend_nodes;\n        proxy_set_header Host \$host;\n        proxy_set_header X-Real-IP \$remote_addr;\n        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto \$scheme;\n    }\n}\n" > "$CONF_FILE"
}

main() {
    require_root
    [ -n "$BACKENDS" ] || die "Set BACKENDS or pass backend arguments."

    backup_config
    write_nginx_config

    nginx -t
    systemctl reload nginx

    log "Backend update completed."
    echo "[INFO] Backend default port: ${BACKEND_PORT}"
    echo "[INFO] Backends: ${BACKENDS}"
}

main "$@"
