#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# Minimal DB setup for zzaphub email verification API tests.
# Default network: VMware VMnet8 NAT, 192.168.240.0/24.

MODE="${1:-all}"

RUN_NETPLAN="${RUN_NETPLAN:-0}"
NET_IFACE="${NET_IFACE:-}"
DB_IP_CIDR="${DB_IP_CIDR:-192.168.240.20/24}"
WEB_IP="${WEB_IP:-192.168.240.10}"
GATEWAY="${GATEWAY:-192.168.240.2}"
DNS_SERVERS="${DNS_SERVERS:-8.8.8.8,1.1.1.1}"
NETPLAN_FILE="${NETPLAN_FILE:-/etc/netplan/99-zzaphub-email-test.yaml}"

DB_NAME="${DB_NAME:-}"
DB_USER="${DB_USER:-}"
DB_PASSWORD="${DB_PASSWORD:-}"
TEST_LOGIN_ID="${TEST_LOGIN_ID:-}"
TEST_EMAIL="${TEST_EMAIL:-}"
ALLOW_UFW="${ALLOW_UFW:-1}"
ENV_FILE="${ENV_FILE:-/etc/zzaphub-email-test.env}"

log() {
    echo "[INFO] $*"
}

warn() {
    echo "[WARN] $*" >&2
}

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage:
  sudo bash 'db-email-test(5.7).sh' [all|netplan|db|status]

Defaults:
  DB IP:       192.168.240.20/24
  WEB IP:      192.168.240.10
  Gateway:     192.168.240.2
  DNS:         8.8.8.8,1.1.1.1
  DB name:     care
  DB user:     web
  DB password: 7898
  Netplan:     skipped in all mode. Run netplan mode explicitly if needed.

Overrides:
  RUN_NETPLAN=1
  NET_IFACE=ens33
  DB_IP_CIDR=192.168.240.20/24
  WEB_IP=192.168.240.10
  DB_PASSWORD='...'
  TEST_LOGIN_ID=email_test
  ENV_FILE=/etc/zzaphub-email-test.env
EOF
}

require_root() {
    if [ "${EUID}" -ne 0 ]; then
        die "Run as root. Example: sudo bash '$0'"
    fi
}

validate_plain_value() {
    local name="$1"
    local value="$2"

    case "${value}" in
        *"'"*|*$'\n'*|*$'\r'*)
            die "${name} must not contain single quote or newline."
            ;;
    esac
}

can_prompt_values() {
    [ -t 0 ] && [ -t 1 ]
}

env_file_value() {
    local key="$1"

    [ -f "${ENV_FILE}" ] || return 1
    (
        set +u
        # shellcheck disable=SC1090
        . "${ENV_FILE}"
        eval "printf '%s' \"\${${key}:-}\""
    )
}

set_from_env_file_if_empty() {
    local key="$1"
    local var_name="$2"
    local value

    [ -z "${!var_name:-}" ] || return 0
    value="$(env_file_value "${key}" 2>/dev/null || true)"
    [ -n "${value}" ] || return 0
    printf -v "${var_name}" '%s' "${value}"
}

load_env_file_defaults() {
    set_from_env_file_if_empty "DB_NAME" "DB_NAME"
    set_from_env_file_if_empty "DB_USER" "DB_USER"
    set_from_env_file_if_empty "DB_PASSWORD" "DB_PASSWORD"
    set_from_env_file_if_empty "MASTER_DB_PASSWORD" "DB_PASSWORD"
    set_from_env_file_if_empty "TEST_LOGIN_ID" "TEST_LOGIN_ID"
    set_from_env_file_if_empty "TEST_EMAIL" "TEST_EMAIL"
}

apply_defaults() {
    DB_NAME="${DB_NAME:-care}"
    DB_USER="${DB_USER:-web}"
    TEST_LOGIN_ID="${TEST_LOGIN_ID:-email_test}"
}

prompt_input_if_needed() {
    local key="$1"
    local label="$2"
    local var_name="$3"
    local secret="$4"
    local default_value="${5:-}"
    local answer

    [ -n "${!var_name:-}" ] && return 0

    if ! can_prompt_values; then
        return 1
    fi

    if [ "${secret}" = "1" ]; then
        if [ -n "${default_value}" ]; then
            printf "%s [Enter=default]: " "${label}"
        else
            printf "%s: " "${label}"
        fi
        IFS= read -r -s answer
        printf "\n"
    else
        if [ -n "${default_value}" ]; then
            printf "%s [default: %s]: " "${label}" "${default_value}"
        else
            printf "%s: " "${label}"
        fi
        IFS= read -r answer
    fi

    if [ -z "${answer}" ] && [ -n "${default_value}" ]; then
        answer="${default_value}"
    fi

    [ -n "${answer}" ] || return 1
    printf -v "${var_name}" '%s' "${answer}"
    validate_plain_value "${key}" "${!var_name}"
}

quote_env_value() {
    local value="$1"

    validate_plain_value "env value" "${value}"
    printf "'%s'" "${value}"
}

print_missing_input_help() {
    local missing_names="$*"

    warn "Missing required values: ${missing_names}"
    warn "Run this script from an interactive terminal, or create ${ENV_FILE} manually."
    cat >&2 <<EOF

${ENV_FILE} example:
DB_NAME='care'
DB_USER='web'
DB_PASSWORD='7898'
TEST_LOGIN_ID='email_test'
TEST_EMAIL='receiver@example.com'
EOF
}

ensure_db_inputs() {
    local missing=()

    prompt_input_if_needed "DB_PASSWORD" "DB password for ${DB_USER}@${WEB_IP}" "DB_PASSWORD" "1" "7898" || missing+=("DB_PASSWORD")
    prompt_input_if_needed "TEST_EMAIL" "Receiver email for test" "TEST_EMAIL" "0" "" || missing+=("TEST_EMAIL")

    if [ "${#missing[@]}" -ne 0 ]; then
        print_missing_input_help "${missing[@]}"
        die "Cannot continue without DB test inputs."
    fi

    validate_plain_value "DB_NAME" "${DB_NAME}"
    validate_plain_value "DB_USER" "${DB_USER}"
    validate_plain_value "DB_PASSWORD" "${DB_PASSWORD}"
    validate_plain_value "TEST_LOGIN_ID" "${TEST_LOGIN_ID}"
    validate_plain_value "TEST_EMAIL" "${TEST_EMAIL}"
}

write_env_file() {
    log "Write test DB environment file. Secret values are not printed: ${ENV_FILE}"
    install -d -m 755 "$(dirname "${ENV_FILE}")"
    cat > "${ENV_FILE}" <<EOF
DB_NAME=$(quote_env_value "${DB_NAME}")
DB_USER=$(quote_env_value "${DB_USER}")
DB_PASSWORD=$(quote_env_value "${DB_PASSWORD}")
TEST_LOGIN_ID=$(quote_env_value "${TEST_LOGIN_ID}")
TEST_EMAIL=$(quote_env_value "${TEST_EMAIL}")
EOF
    chmod 600 "${ENV_FILE}"
    chown root:root "${ENV_FILE}" 2>/dev/null || true
}

detect_iface() {
    if [ -n "${NET_IFACE}" ]; then
        echo "${NET_IFACE}"
        return 0
    fi

    ip -o link show | awk -F': ' '$2 != "lo" { print $2; exit }'
}

write_netplan() {
    local iface
    local dns_yaml

    if [ "${RUN_NETPLAN}" != "1" ]; then
        warn "RUN_NETPLAN=0, skip netplan."
        return 0
    fi

    iface="$(detect_iface)"
    [ -n "${iface}" ] || die "Could not detect network interface. Set NET_IFACE=ens33."
    dns_yaml="$(printf '%s' "${DNS_SERVERS}" | sed 's/,/, /g')"

    log "Write static netplan: ${NETPLAN_FILE}"
    cat > "${NETPLAN_FILE}" <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    ${iface}:
      dhcp4: false
      addresses:
        - ${DB_IP_CIDR}
      routes:
        - to: default
          via: ${GATEWAY}
      nameservers:
        addresses: [${dns_yaml}]
EOF

    chmod 600 "${NETPLAN_FILE}"
    netplan generate
    netplan apply
    log "Static IP applied to ${iface}: ${DB_IP_CIDR}"
}

install_mariadb() {
    log "Install MariaDB packages."
    apt update
    apt install -y mariadb-server mariadb-client
    systemctl enable --now mariadb
}

configure_mariadb_bind() {
    local conf="/etc/mysql/mariadb.conf.d/50-server.cnf"

    if [ -f "${conf}" ]; then
        sed -i 's/^[[:space:]]*bind-address[[:space:]]*=.*/bind-address = 0.0.0.0/' "${conf}"
    else
        warn "MariaDB server config not found: ${conf}"
    fi
}

setup_schema_and_user() {
    validate_plain_value "DB_NAME" "${DB_NAME}"
    validate_plain_value "DB_USER" "${DB_USER}"
    validate_plain_value "DB_PASSWORD" "${DB_PASSWORD}"
    validate_plain_value "TEST_LOGIN_ID" "${TEST_LOGIN_ID}"
    validate_plain_value "TEST_EMAIL" "${TEST_EMAIL}"

    log "Create test database, user, tables, and test user row."
    mariadb -uroot <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS '${DB_USER}'@'${WEB_IP}' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'${WEB_IP}' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'${WEB_IP}';
FLUSH PRIVILEGES;

USE ${DB_NAME};

CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  login_id VARCHAR(255) UNIQUE NOT NULL,
  pw VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(255),
  point INT DEFAULT 0,
  role ENUM('USER', 'ADMIN') DEFAULT 'USER',
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blacklist (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) UNIQUE,
  reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  category VARCHAR(255),
  title VARCHAR(255) NOT NULL,
  content TEXT,
  view_count INT DEFAULT 0,
  file_name VARCHAR(500),
  status VARCHAR(20) DEFAULT 'NORMAL',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DELETE FROM blacklist WHERE email='${TEST_EMAIL}';
DELETE FROM users WHERE login_id='${TEST_LOGIN_ID}' OR email='${TEST_EMAIL}';
INSERT INTO users (login_id, pw, name, email, phone, is_verified)
VALUES ('${TEST_LOGIN_ID}', 'email-test-password-not-for-login', 'Email Test User', '${TEST_EMAIL}', '010-0000-0000', false);
EOF
}

open_firewall() {
    if [ "${ALLOW_UFW}" != "1" ]; then
        warn "ALLOW_UFW=0, skip ufw."
        return 0
    fi

    if command -v ufw >/dev/null 2>&1; then
        ufw allow 3306/tcp || true
    else
        warn "ufw not found. Check firewall manually if DB connection fails."
    fi
}

restart_and_status() {
    systemctl restart mariadb
    systemctl --no-pager --full status mariadb || true
}

print_report() {
    local db_ip

    db_ip="${DB_IP_CIDR%%/*}"

    cat <<EOF

[EMAIL TEST DB INFO]
DB: ${db_ip}
WEB allowed DB client: ${WEB_IP}
DB name: ${DB_NAME}
DB user: ${DB_USER}
TEST_EMAIL: ${TEST_EMAIL:-not-set}

[CHECK]
sudo mariadb -uroot -e "USE ${DB_NAME}; SELECT login_id,email,is_verified FROM users WHERE login_id='${TEST_LOGIN_ID}';"
sudo mariadb -uroot -e "USE ${DB_NAME}; SELECT login_id,email,is_verified FROM users WHERE email='${TEST_EMAIL:-receiver@example.com}';"
sudo mariadb -uroot -e "USE ${DB_NAME}; SELECT email,reason,created_at FROM blacklist WHERE email='${TEST_EMAIL:-receiver@example.com}';"
sudo mariadb -uroot -e "USE ${DB_NAME}; SHOW TABLES LIKE 'posts';"
sudo ss -ltnp | grep 3306
EOF
}

print_db_checks() {
    if ! command -v mariadb >/dev/null 2>&1; then
        warn "mariadb client not found. Cannot run DB checks."
        return 0
    fi

    validate_plain_value "DB_NAME" "${DB_NAME}"
    validate_plain_value "TEST_LOGIN_ID" "${TEST_LOGIN_ID}"
    validate_plain_value "TEST_EMAIL" "${TEST_EMAIL:-}"

    echo
    echo "[DB CHECK: by login_id]"
    mariadb -uroot -e "USE ${DB_NAME}; SELECT id,login_id,email,is_verified FROM users WHERE login_id='${TEST_LOGIN_ID}';" || true

    if [ -n "${TEST_EMAIL}" ]; then
        echo
        echo "[DB CHECK: by email]"
        mariadb -uroot -e "USE ${DB_NAME}; SELECT id,login_id,email,is_verified FROM users WHERE email='${TEST_EMAIL}';" || true

        echo
        echo "[DB CHECK: blacklist]"
        mariadb -uroot -e "USE ${DB_NAME}; SELECT id,email,reason,created_at FROM blacklist WHERE email='${TEST_EMAIL}';" || true
    else
        warn "TEST_EMAIL is not set, skip email and blacklist checks."
    fi
}

run_db() {
    ensure_db_inputs
    write_env_file
    install_mariadb
    configure_mariadb_bind
    setup_schema_and_user
    open_firewall
    restart_and_status
}

main() {
    case "${MODE}" in
        -h|--help|help)
            usage
            exit 0
            ;;
        all|netplan|db|status)
            ;;
        *)
            usage
            die "Unsupported mode: ${MODE}"
            ;;
    esac

    require_root
    load_env_file_defaults
    apply_defaults

    case "${MODE}" in
        all)
            write_netplan
            run_db
            print_report
            ;;
        netplan)
            RUN_NETPLAN=1
            write_netplan
            ;;
        db)
            run_db
            print_report
            ;;
        status)
            systemctl --no-pager --full status mariadb || true
            print_db_checks
            print_report
            ;;
    esac
}

main "$@"
