#!/usr/bin/env bash
set -euo pipefail

# Promtail + Node Exporter setup script.
#
# This script follows the class copy-paste setup, with only the Loki IP changed
# to this project's public/NAT IP.
#
# Usage:
#   sudo bash promtail-client.sh PRESET [HOST_LABEL]
#
# Presets:
#   web    -> host default: webserv
#   db     -> host default: dbserv
#   lb     -> host default: lbserv
#   redis  -> host default: redisserv
#   nfs    -> host default: nfsserv
#   dns    -> host default: dnsserv
#   log    -> host default: logserv
#   system -> host default: current hostname
#
# Project copy-paste commands:
#   sudo bash promtail-client.sh web
#   sudo bash promtail-client.sh db
#   sudo bash promtail-client.sh lb
#   sudo bash promtail-client.sh redis
#   sudo bash promtail-client.sh nfs
#   sudo bash promtail-client.sh dns
#   sudo bash promtail-client.sh log
#
# If the host label must be forced:
#   sudo bash promtail-client.sh web webserv
#
# Note:
#   The web preset is for the CARE PHP/Apache web server, not Tomcat.

PROMTAIL_VERSION="2.9.4"
LOKI_PUSH_URL="${LOKI_PUSH_URL:-http://1.1.3.11:3100/loki/api/v1/push}"
CONFIG_FILE="/etc/promtail/config.yml"
SERVICE_FILE="/etc/systemd/system/promtail.service"
PRESET="${1:-}"
HOST_LABEL="${2:-}"

usage() {
    cat <<'EOF'
Usage:
  sudo bash promtail-client.sh PRESET [HOST_LABEL]

Presets:
  web | db | lb | redis | nfs | dns | log | system

Examples:
  sudo bash promtail-client.sh web
  sudo bash promtail-client.sh lb
  sudo bash promtail-client.sh system server1
EOF
}

need_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        echo "[ERROR] Run with sudo: sudo bash promtail-client.sh PRESET [HOST_LABEL]" >&2
        exit 1
    fi
}

default_host_for_preset() {
    case "$1" in
        web) echo "webserv" ;;
        db) echo "dbserv" ;;
        lb) echo "lbserv" ;;
        redis) echo "redisserv" ;;
        nfs) echo "nfsserv" ;;
        dns) echo "dnsserv" ;;
        log) echo "logserv" ;;
        system) hostname ;;
        *) return 1 ;;
    esac
}

write_promtail_config() {
    mkdir -p "$(dirname "${CONFIG_FILE}")"

    case "${PRESET}" in
        web)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
- url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
- job_name: apache
  static_configs:
  - targets:
      - localhost
    labels:
      job: apachelogs
      host: ${HOST_LABEL}
      __path__: /var/log/apache2/*.log
EOF
            ;;
        db)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
- url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
- job_name: mariadb
  static_configs:
  - targets:
      - localhost
    labels:
      job: dblogs
      host: ${HOST_LABEL}
      __path__: /var/log/mysql/error.log
EOF
            ;;
        lb)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
- url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
- job_name: nginx
  static_configs:
  - targets:
      - localhost
    labels:
      job: lblogs
      host: ${HOST_LABEL}
      __path__: /var/log/nginx/*.log
EOF
            ;;
        redis)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
- url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
- job_name: redis
  static_configs:
  - targets:
      - localhost
    labels:
      job: redislogs
      host: ${HOST_LABEL}
      __path__: /var/log/redis/redis-server.log
EOF
            ;;
        nfs)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
- url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
- job_name: nfs
  static_configs:
  - targets:
      - localhost
    labels:
      job: nfslogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
EOF
            ;;
        dns)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
- url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
- job_name: bind9
  static_configs:
  - targets:
      - localhost
    labels:
      job: dnslogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
EOF
            ;;
        log)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
- url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/syslog
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
EOF
            ;;
        system)
            cat > "${CONFIG_FILE}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
  - url: ${LOKI_PUSH_URL}
scrape_configs:
- job_name: system
  static_configs:
  - targets:
      - localhost
    labels:
      job: varlogs
      host: ${HOST_LABEL}
      __path__: /var/log/*log
- job_name: auth
  static_configs:
  - targets:
      - localhost
    labels:
      job: authlogs
      host: ${HOST_LABEL}
      __path__: /var/log/auth.log
EOF
            ;;
    esac
}

write_promtail_service() {
    cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Promtail service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/promtail -config.file=/etc/promtail/config.yml
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
}

need_root

if [[ -z "${PRESET}" ]]; then
    usage
    exit 1
fi

if ! HOST_LABEL_DEFAULT="$(default_host_for_preset "${PRESET}")"; then
    usage
    echo "[ERROR] Unsupported preset: ${PRESET}" >&2
    exit 1
fi

if [[ -z "${HOST_LABEL}" ]]; then
    HOST_LABEL="${HOST_LABEL_DEFAULT}"
fi

echo "[INFO] preset=${PRESET}"
echo "[INFO] host=${HOST_LABEL}"
echo "[INFO] loki=${LOKI_PUSH_URL}"

echo "[STEP 1] Installing Node Exporter"
apt-get update
apt-get install -y prometheus-node-exporter
systemctl enable --now prometheus-node-exporter

echo "[STEP 2] Downloading Promtail ${PROMTAIL_VERSION}"
cd /tmp
curl -O -L "https://github.com/grafana/loki/releases/download/v${PROMTAIL_VERSION}/promtail-linux-amd64.zip"
apt-get install -y unzip
unzip -o promtail-linux-amd64.zip
mv promtail-linux-amd64 /usr/local/bin/promtail
chmod +x /usr/local/bin/promtail

echo "[STEP 3] Writing Promtail config: ${CONFIG_FILE}"
write_promtail_config

echo "[STEP 4] Writing Promtail service: ${SERVICE_FILE}"
write_promtail_service

echo "[STEP 5] Enabling and restarting Promtail"
useradd --no-create-home --shell /bin/false promtail 2>/dev/null || true
usermod -aG adm promtail 2>/dev/null || true
systemctl daemon-reload
systemctl enable --now promtail
systemctl restart promtail

echo "=== Node Exporter ==="
systemctl is-active prometheus-node-exporter
echo "=== Promtail ==="
systemctl is-active promtail

echo "[INFO] Check config:"
echo "  sudo grep -nE 'url:|host:|__path__' /etc/promtail/config.yml"
echo "[INFO] Grafana Loki query:"
echo "  {host=\"${HOST_LABEL}\"}"
