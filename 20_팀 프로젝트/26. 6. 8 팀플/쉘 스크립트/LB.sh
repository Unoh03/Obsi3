#!/bin/bash
set -euo pipefail

# Single nginx load balancer setup for one LB node.
#
# Usage:
#   sudo BACKENDS="WEB1_IP WEB2_IP" bash LB.sh
#   sudo bash LB.sh WEB1_IP WEB2_IP
#
# Optional:
#   LISTEN_PORT=80
#   BACKEND_PORT=80
#   CONF_FILE=/etc/nginx/conf.d/project-load-balancer.conf

LISTEN_PORT="${LISTEN_PORT:-80}"
BACKEND_PORT="${BACKEND_PORT:-80}"
CONF_FILE="${CONF_FILE:-/etc/nginx/conf.d/project-load-balancer.conf}"
BACKENDS="${BACKENDS:-${*:-}}"

log() {
    echo "[INFO] $*"
}

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "Run as root. Example: sudo BACKENDS='WEB1_IP WEB2_IP' bash LB.sh"
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

write_nginx_config() {
    local upstream=""
    local backend

    for backend in $BACKENDS; do
        backend="$(normalize_backend "$backend")"
        upstream="${upstream}    server ${backend};\n"
    done

    [ -n "$upstream" ] || die "No backend provided."

    log "Writing nginx load balancer config to ${CONF_FILE}."
    printf '%b' "upstream backend_nodes {\n${upstream}}\n\nserver {\n    listen ${LISTEN_PORT};\n    server_name _;\n\n    location / {\n        proxy_pass http://backend_nodes;\n        proxy_set_header Host \$host;\n        proxy_set_header X-Real-IP \$remote_addr;\n        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto \$scheme;\n    }\n}\n" > "$CONF_FILE"
}

main() {
    require_root

    [ -n "$BACKENDS" ] || die "Set BACKENDS or pass backend arguments."

    log "Installing nginx."
    apt update
    apt install -y nginx

    write_nginx_config
    rm -f /etc/nginx/sites-enabled/default

    log "Testing nginx config."
    nginx -t

    log "Starting nginx."
    systemctl enable nginx
    systemctl restart nginx

    log "Load balancer setup completed."
    echo "[INFO] Listen port: ${LISTEN_PORT}"
    echo "[INFO] Backend default port: ${BACKEND_PORT}"
    echo "[INFO] Backends: ${BACKENDS}"
    echo "[INFO] Check: curl -i http://127.0.0.1:${LISTEN_PORT}/"
}

main "$@"
