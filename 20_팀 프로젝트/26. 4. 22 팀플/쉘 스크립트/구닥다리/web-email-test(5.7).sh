#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# Minimal WEB setup for zzaphub email verification API tests.
# Default network: VMware VMnet8 NAT, 192.168.240.0/24.
# Runtime: external Tomcat 10 + ROOT.war, close to the real deployment path.

MODE="${1:-all}"

RUN_NETPLAN="${RUN_NETPLAN:-0}"
NET_IFACE="${NET_IFACE:-}"
WEB_IP_CIDR="${WEB_IP_CIDR:-192.168.240.10/24}"
DB_IP="${DB_IP:-192.168.240.20}"
GATEWAY="${GATEWAY:-192.168.240.2}"
DNS_SERVERS="${DNS_SERVERS:-8.8.8.8,1.1.1.1}"
NETPLAN_FILE="${NETPLAN_FILE:-/etc/netplan/99-zzaphub-email-test.yaml}"

PROJECT_DIR="${PROJECT_DIR:-/opt/zzaphub}"
GIT_REPO="${GIT_REPO:-https://github.com/SUS7898/zzaphub.git}"
GIT_BRANCH="${GIT_BRANCH:-}"

DB_NAME="${DB_NAME:-}"
DB_USER="${DB_USER:-}"
DB_PASSWORD="${DB_PASSWORD:-}"
MASTER_DB_URL="${MASTER_DB_URL:-}"
MASTER_DB_USER="${MASTER_DB_USER:-}"
MASTER_DB_PASSWORD="${MASTER_DB_PASSWORD:-}"
SLAVE_DB_URL="${SLAVE_DB_URL:-}"
SLAVE_DB_USER="${SLAVE_DB_USER:-}"
SLAVE_DB_PASSWORD="${SLAVE_DB_PASSWORD:-}"

MAIL_USERNAME="${MAIL_USERNAME:-}"
MAIL_PASSWORD="${MAIL_PASSWORD:-}"
TEST_LOGIN_ID="${TEST_LOGIN_ID:-}"
TEST_EMAIL="${TEST_EMAIL:-}"

TOMCAT_VER="${TOMCAT_VER:-10.1.54}"
TOMCAT_BASE="${TOMCAT_BASE:-/opt/tomcat}"
TOMCAT_HOME="${TOMCAT_HOME:-${TOMCAT_BASE}/tomcat-10}"
TOMCAT_USER="${TOMCAT_USER:-tomcat}"
TOMCAT_GROUP="${TOMCAT_GROUP:-tomcat}"
SERVICE_NAME="${SERVICE_NAME:-tomcat.service}"
APP_CONTEXT="${APP_CONTEXT:-ROOT}"
ENV_FILE="${ENV_FILE:-/etc/zzaphub-email-test.env}"
ALLOW_UFW="${ALLOW_UFW:-1}"

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
  sudo bash 'web-email-test(5.7).sh' [all|netplan|packages|repo|config|build|tomcat|deploy|status|db-check]

Defaults:
  WEB IP:    192.168.240.10/24
  DB IP:     192.168.240.20
  Gateway:   192.168.240.2
  Branch:    unoh
  Project:   /opt/zzaphub
  Runtime:   Tomcat 10, ROOT.war, http://WEB:8080/
  Netplan:   skipped in all mode. Run netplan mode explicitly if needed.

Overrides:
  RUN_NETPLAN=1
  NET_IFACE=ens33
  DB_PASSWORD='...'
  GIT_BRANCH=unoh
  PROJECT_DIR=/opt/zzaphub
  ENV_FILE=/etc/zzaphub-email-test.env
EOF
}

require_root() {
    if [ "${EUID}" -ne 0 ]; then
        die "Run as root. Example: sudo bash '$0'"
    fi
}

validate_env_value() {
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
    set_from_env_file_if_empty "GIT_BRANCH" "GIT_BRANCH"
    set_from_env_file_if_empty "DB_NAME" "DB_NAME"
    set_from_env_file_if_empty "DB_USER" "DB_USER"
    set_from_env_file_if_empty "DB_PASSWORD" "DB_PASSWORD"
    set_from_env_file_if_empty "MASTER_DB_URL" "MASTER_DB_URL"
    set_from_env_file_if_empty "MASTER_DB_USER" "MASTER_DB_USER"
    set_from_env_file_if_empty "MASTER_DB_PASSWORD" "MASTER_DB_PASSWORD"
    set_from_env_file_if_empty "SLAVE_DB_URL" "SLAVE_DB_URL"
    set_from_env_file_if_empty "SLAVE_DB_USER" "SLAVE_DB_USER"
    set_from_env_file_if_empty "SLAVE_DB_PASSWORD" "SLAVE_DB_PASSWORD"
    set_from_env_file_if_empty "MAIL_USERNAME" "MAIL_USERNAME"
    set_from_env_file_if_empty "MAIL_PASSWORD" "MAIL_PASSWORD"
    set_from_env_file_if_empty "TEST_LOGIN_ID" "TEST_LOGIN_ID"
    set_from_env_file_if_empty "TEST_EMAIL" "TEST_EMAIL"

    if [ -z "${DB_PASSWORD}" ] && [ -n "${MASTER_DB_PASSWORD}" ]; then
        DB_PASSWORD="${MASTER_DB_PASSWORD}"
    fi
}

apply_defaults() {
    GIT_BRANCH="${GIT_BRANCH:-unoh}"
    DB_NAME="${DB_NAME:-care}"
    DB_USER="${DB_USER:-web}"
    TEST_LOGIN_ID="${TEST_LOGIN_ID:-email_test}"

    MASTER_DB_URL="${MASTER_DB_URL:-jdbc:mariadb://${DB_IP}:3306/${DB_NAME}}"
    MASTER_DB_USER="${MASTER_DB_USER:-${DB_USER}}"
    MASTER_DB_PASSWORD="${MASTER_DB_PASSWORD:-${DB_PASSWORD}}"
    SLAVE_DB_URL="${SLAVE_DB_URL:-jdbc:mariadb://${DB_IP}:3306/${DB_NAME}}"
    SLAVE_DB_USER="${SLAVE_DB_USER:-${DB_USER}}"
    SLAVE_DB_PASSWORD="${SLAVE_DB_PASSWORD:-${DB_PASSWORD}}"
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
    validate_env_value "${key}" "${!var_name}"
}

print_missing_input_help() {
    local missing_names="$*"

    warn "Missing required values: ${missing_names}"
    warn "Run this script from an interactive terminal, or create ${ENV_FILE} manually."
    cat >&2 <<EOF

${ENV_FILE} example:
GIT_BRANCH='unoh'
DB_NAME='care'
DB_USER='web'
DB_PASSWORD='7898'
MAIL_USERNAME='sender@gmail.com'
MAIL_PASSWORD='gmail-app-password'
TEST_LOGIN_ID='email_test'
TEST_EMAIL='receiver@example.com'
EOF
}

ensure_db_inputs() {
    local missing=()

    prompt_input_if_needed "DB_PASSWORD" "DB password for ${DB_USER}@${DB_IP}" "DB_PASSWORD" "1" "7898" || missing+=("DB_PASSWORD")
    prompt_input_if_needed "TEST_EMAIL" "Receiver email for test" "TEST_EMAIL" "0" "" || missing+=("TEST_EMAIL")

    if [ "${#missing[@]}" -ne 0 ]; then
        print_missing_input_help "${missing[@]}"
        die "Cannot continue without DB test inputs."
    fi

    apply_defaults
    MASTER_DB_PASSWORD="${MASTER_DB_PASSWORD:-${DB_PASSWORD}}"
    SLAVE_DB_PASSWORD="${SLAVE_DB_PASSWORD:-${DB_PASSWORD}}"
    validate_env_value "DB_NAME" "${DB_NAME}"
    validate_env_value "DB_USER" "${DB_USER}"
    validate_env_value "DB_PASSWORD" "${DB_PASSWORD}"
    validate_env_value "MASTER_DB_URL" "${MASTER_DB_URL}"
    validate_env_value "MASTER_DB_USER" "${MASTER_DB_USER}"
    validate_env_value "MASTER_DB_PASSWORD" "${MASTER_DB_PASSWORD}"
    validate_env_value "SLAVE_DB_URL" "${SLAVE_DB_URL}"
    validate_env_value "SLAVE_DB_USER" "${SLAVE_DB_USER}"
    validate_env_value "SLAVE_DB_PASSWORD" "${SLAVE_DB_PASSWORD}"
    validate_env_value "TEST_LOGIN_ID" "${TEST_LOGIN_ID}"
    validate_env_value "TEST_EMAIL" "${TEST_EMAIL}"
}

ensure_web_inputs() {
    local missing=()

    ensure_db_inputs
    prompt_input_if_needed "MAIL_USERNAME" "Gmail sender address" "MAIL_USERNAME" "0" "" || missing+=("MAIL_USERNAME")
    prompt_input_if_needed "MAIL_PASSWORD" "Gmail app password" "MAIL_PASSWORD" "1" "" || missing+=("MAIL_PASSWORD")

    if [ "${#missing[@]}" -ne 0 ]; then
        print_missing_input_help "${missing[@]}"
        die "Cannot continue without mail inputs."
    fi

    MAIL_PASSWORD="$(printf '%s' "${MAIL_PASSWORD}" | tr -d ' ')"
    validate_env_value "MAIL_USERNAME" "${MAIL_USERNAME}"
    validate_env_value "MAIL_PASSWORD" "${MAIL_PASSWORD}"
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
        - ${WEB_IP_CIDR}
      routes:
        - to: default
          via: ${GATEWAY}
      nameservers:
        addresses: [${dns_yaml}]
EOF

    chmod 600 "${NETPLAN_FILE}"
    netplan generate
    netplan apply
    log "Static IP applied to ${iface}: ${WEB_IP_CIDR}"
}

install_packages() {
    log "Install WEB packages."
    apt update
    apt install -y openjdk-17-jdk git maven curl wget tar mariadb-client
}

prepare_repo() {
    if [ -d "${PROJECT_DIR}/.git" ]; then
        log "Use existing repo: ${PROJECT_DIR}"
        git -C "${PROJECT_DIR}" fetch origin
        git -C "${PROJECT_DIR}" switch "${GIT_BRANCH}" 2>/dev/null || git -C "${PROJECT_DIR}" switch -c "${GIT_BRANCH}" "origin/${GIT_BRANCH}"
        git -C "${PROJECT_DIR}" pull --ff-only origin "${GIT_BRANCH}"
        return 0
    fi

    if [ -e "${PROJECT_DIR}" ]; then
        die "PROJECT_DIR exists but is not a git repository: ${PROJECT_DIR}"
    fi

    log "Clone zzaphub repo: ${GIT_REPO}, branch=${GIT_BRANCH}"
    git clone --branch "${GIT_BRANCH}" "${GIT_REPO}" "${PROJECT_DIR}"
}

quote_env_value() {
    local value="$1"

    validate_env_value "env value" "${value}"
    printf "'%s'" "${value}"
}

write_env_file() {
    ensure_web_inputs

    log "Write Tomcat environment file. Secret values are not printed: ${ENV_FILE}"
    install -d -m 755 "$(dirname "${ENV_FILE}")"
    cat > "${ENV_FILE}" <<EOF
GIT_BRANCH=$(quote_env_value "${GIT_BRANCH}")
DB_NAME=$(quote_env_value "${DB_NAME}")
DB_USER=$(quote_env_value "${DB_USER}")
DB_PASSWORD=$(quote_env_value "${DB_PASSWORD}")
MASTER_DB_URL=$(quote_env_value "${MASTER_DB_URL}")
MASTER_DB_USER=$(quote_env_value "${MASTER_DB_USER}")
MASTER_DB_PASSWORD=$(quote_env_value "${MASTER_DB_PASSWORD}")
SLAVE_DB_URL=$(quote_env_value "${SLAVE_DB_URL}")
SLAVE_DB_USER=$(quote_env_value "${SLAVE_DB_USER}")
SLAVE_DB_PASSWORD=$(quote_env_value "${SLAVE_DB_PASSWORD}")
MAIL_USERNAME=$(quote_env_value "${MAIL_USERNAME}")
MAIL_PASSWORD=$(quote_env_value "${MAIL_PASSWORD}")
TEST_LOGIN_ID=$(quote_env_value "${TEST_LOGIN_ID}")
TEST_EMAIL=$(quote_env_value "${TEST_EMAIL}")
EOF
    chmod 600 "${ENV_FILE}"
    chown root:root "${ENV_FILE}" 2>/dev/null || true
}

write_application_properties() {
    local prop_file="${PROJECT_DIR}/src/main/resources/application.properties"

    log "Write server-read application.properties: ${prop_file}"
    install -d -m 755 "$(dirname "${prop_file}")"
    cat > "${prop_file}" <<'EOF'
spring.application.name=zzaphub

spring.datasource.master.driver-class-name=org.mariadb.jdbc.Driver
spring.datasource.master.jdbc-url=${MASTER_DB_URL}
spring.datasource.master.username=${MASTER_DB_USER}
spring.datasource.master.password=${MASTER_DB_PASSWORD}

spring.datasource.slave.driver-class-name=org.mariadb.jdbc.Driver
spring.datasource.slave.jdbc-url=${SLAVE_DB_URL}
spring.datasource.slave.username=${SLAVE_DB_USER}
spring.datasource.slave.password=${SLAVE_DB_PASSWORD}

mybatis.mapper-locations=/mappers/*.xml

spring.mvc.view.prefix=/jsp/
spring.mvc.view.suffix=.jsp

spring.servlet.multipart.max-file-size=10MB

spring.mail.host=smtp.gmail.com
spring.mail.port=587
spring.mail.username=${MAIL_USERNAME}
spring.mail.password=${MAIL_PASSWORD}
spring.mail.properties.mail.smtp.auth=true
spring.mail.properties.mail.smtp.starttls.enable=true
spring.mail.properties.mail.smtp.starttls.required=true
EOF
}

configure_app() {
    prepare_repo
    write_env_file
    write_application_properties
}

build_war() {
    log "Build WAR: mvn clean package -DskipTests"
    (
        cd "${PROJECT_DIR}"
        mvn clean package -DskipTests
    )
}

ensure_tomcat_user() {
    if id "${TOMCAT_USER}" >/dev/null 2>&1; then
        return 0
    fi

    useradd -r -m -U -d "${TOMCAT_BASE}" -s /bin/false "${TOMCAT_USER}"
}

download_tomcat() {
    local tarball="$1"
    local primary="https://downloads.apache.org/tomcat/tomcat-10/v${TOMCAT_VER}/bin/apache-tomcat-${TOMCAT_VER}.tar.gz"
    local archive="https://archive.apache.org/dist/tomcat/tomcat-10/v${TOMCAT_VER}/bin/apache-tomcat-${TOMCAT_VER}.tar.gz"

    if wget -O "${tarball}" "${primary}"; then
        return 0
    fi

    warn "Primary Tomcat download failed. Try archive."
    wget -O "${tarball}" "${archive}"
}

install_tomcat() {
    local tmp_dir
    local tarball
    local extracted_dir

    ensure_tomcat_user

    if [ -x "${TOMCAT_HOME}/bin/startup.sh" ]; then
        log "Tomcat already installed: ${TOMCAT_HOME}"
        return 0
    fi

    install -d -m 755 -o "${TOMCAT_USER}" -g "${TOMCAT_GROUP}" "${TOMCAT_BASE}"
    tmp_dir="$(mktemp -d)"
    tarball="${tmp_dir}/apache-tomcat-${TOMCAT_VER}.tar.gz"
    extracted_dir="${TOMCAT_BASE}/apache-tomcat-${TOMCAT_VER}"

    log "Install Tomcat ${TOMCAT_VER}"
    download_tomcat "${tarball}"
    tar -xf "${tarball}" -C "${TOMCAT_BASE}"
    mv "${extracted_dir}" "${TOMCAT_HOME}"
    chown -R "${TOMCAT_USER}:${TOMCAT_GROUP}" "${TOMCAT_HOME}"
    rm -rf "${tmp_dir}"
}

write_tomcat_service() {
    local service_file="/etc/systemd/system/${SERVICE_NAME}"

    log "Write Tomcat systemd service: ${service_file}"
    cat > "${service_file}" <<EOF
[Unit]
Description=Tomcat 10 servlet container for zzaphub email test
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User=${TOMCAT_USER}
Group=${TOMCAT_GROUP}
EnvironmentFile=${ENV_FILE}
Environment="JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64/"
ExecStart=${TOMCAT_HOME}/bin/startup.sh
ExecStop=${TOMCAT_HOME}/bin/shutdown.sh
SuccessExitStatus=143

[Install]
WantedBy=multi-user.target
EOF

    chmod 644 "${service_file}"
    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}"
}

setup_tomcat() {
    install_tomcat
    write_tomcat_service
}

find_built_war() {
    find "${PROJECT_DIR}/target" -maxdepth 1 -type f -name '*.war' | sort | head -n 1
}

deploy_war() {
    local built_war

    built_war="$(find_built_war)"
    [ -n "${built_war}" ] || die "No WAR found under ${PROJECT_DIR}/target. Run build first."

    systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
    install -d -m 755 -o "${TOMCAT_USER}" -g "${TOMCAT_GROUP}" "${TOMCAT_HOME}/webapps"

    rm -rf "${TOMCAT_HOME}/webapps/${APP_CONTEXT}" "${TOMCAT_HOME}/webapps/${APP_CONTEXT}.war"
    rm -rf "${TOMCAT_HOME}/work/Catalina/localhost/${APP_CONTEXT}" 2>/dev/null || true

    log "Deploy WAR as ${APP_CONTEXT}.war: ${built_war}"
    cp "${built_war}" "${TOMCAT_HOME}/webapps/${APP_CONTEXT}.war"
    chown "${TOMCAT_USER}:${TOMCAT_GROUP}" "${TOMCAT_HOME}/webapps/${APP_CONTEXT}.war"

    systemctl start "${SERVICE_NAME}"
}

open_firewall() {
    if [ "${ALLOW_UFW}" != "1" ]; then
        warn "ALLOW_UFW=0, skip ufw."
        return 0
    fi

    if command -v ufw >/dev/null 2>&1; then
        ufw allow 8080/tcp || true
    else
        warn "ufw not found. Check firewall manually if WEB connection fails."
    fi
}

wait_for_webapp() {
    local waited=0
    local max_wait="${APP_WAIT:-60}"

    while [ "${waited}" -lt "${max_wait}" ]; do
        if curl -fsS --max-time 3 "http://127.0.0.1:8080/" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done

    warn "WEB root check failed after ${max_wait}s. Check: journalctl -u ${SERVICE_NAME} -n 100 --no-pager"
}

check_smtp_network() {
    if getent hosts smtp.gmail.com >/dev/null 2>&1; then
        log "DNS can resolve smtp.gmail.com."
    else
        warn "Cannot resolve smtp.gmail.com. Check DNS/netplan."
    fi

    if timeout 5 bash -c '</dev/tcp/smtp.gmail.com/587' >/dev/null 2>&1; then
        log "Can connect to smtp.gmail.com:587."
    else
        warn "Cannot connect to smtp.gmail.com:587. Check NAT gateway/firewall."
    fi
}

repo_current_branch() {
    if [ -d "${PROJECT_DIR}/.git" ]; then
        git -C "${PROJECT_DIR}" branch --show-current 2>/dev/null || true
    fi
}

repo_origin_url() {
    if [ -d "${PROJECT_DIR}/.git" ]; then
        git -C "${PROJECT_DIR}" remote get-url origin 2>/dev/null || true
    fi
}

tomcat_active_state() {
    systemctl is-active "${SERVICE_NAME}" 2>/dev/null || true
}

run_db_query() {
    local query="$1"
    local defaults_file
    local rc

    command -v mariadb >/dev/null 2>&1 || die "mariadb client is not installed. Run packages mode first."

    defaults_file="$(mktemp)"
    chmod 600 "${defaults_file}"
    cat > "${defaults_file}" <<EOF
[client]
host=${DB_IP}
port=3306
user=${DB_USER}
password=${DB_PASSWORD}
database=${DB_NAME}
connect-timeout=5
EOF

    set +e
    mariadb --defaults-extra-file="${defaults_file}" -e "${query}"
    rc=$?
    set -e
    rm -f "${defaults_file}"
    return "${rc}"
}

check_db_test_user() {
    ensure_db_inputs

    log "Check DB test user from WEB. Password is not printed."
    run_db_query "SELECT id,login_id,email,is_verified FROM users WHERE login_id='${TEST_LOGIN_ID}' OR email='${TEST_EMAIL}'; SELECT id,email,reason,created_at FROM blacklist WHERE email='${TEST_EMAIL}';"
}

status_report() {
    local web_ip
    local username_state="not-set"
    local password_state="not-set"
    local repo_branch="not-a-git-repo"
    local repo_remote="not-a-git-repo"
    local tomcat_state="unknown"

    web_ip="${WEB_IP_CIDR%%/*}"
    [ -n "${MAIL_USERNAME}" ] && username_state="set"
    [ -n "${MAIL_PASSWORD}" ] && password_state="set"
    repo_branch="$(repo_current_branch)"
    repo_remote="$(repo_origin_url)"
    tomcat_state="$(tomcat_active_state)"
    repo_branch="${repo_branch:-not-a-git-repo}"
    repo_remote="${repo_remote:-not-a-git-repo}"
    tomcat_state="${tomcat_state:-unknown}"

    cat <<EOF

[EMAIL TEST WEB INFO]
WEB: ${web_ip}
DB: ${DB_IP}
NAT/Router: VMware VMnet8 NAT gateway ${GATEWAY}
DNS: ${DNS_SERVERS}

zzaphub path: ${PROJECT_DIR}
zzaphub branch: ${repo_branch}
zzaphub remote: ${repo_remote}
Execution: external Tomcat 10, ROOT.war, service=${SERVICE_NAME}, URL=http://${web_ip}:8080/
Tomcat active: ${tomcat_state}
application.properties source: ${PROJECT_DIR}/src/main/resources/application.properties
application.properties runtime: ${TOMCAT_HOME}/webapps/${APP_CONTEXT}/WEB-INF/classes/application.properties
ENV_FILE: ${ENV_FILE}
MAIL_USERNAME: ${username_state}
MAIL_PASSWORD: ${password_state}
TEST_EMAIL: ${TEST_EMAIL:-not-set}

[API TEST EXAMPLES]
curl -X POST http://${web_ip}:8080/api/email-verification/send \\
  -H "Content-Type: application/json" \\
  -d '{"email":"${TEST_EMAIL:-receiver@example.com}","purpose":"SIGNUP"}'

curl -X POST http://${web_ip}:8080/api/email-verification/verify \\
  -H "Content-Type: application/json" \\
  -d '{"email":"${TEST_EMAIL:-receiver@example.com}","purpose":"SIGNUP","code":"1234"}'

[LOG]
journalctl -u ${SERVICE_NAME} -n 80 --no-pager
EOF
}

run_all() {
    write_netplan
    install_packages
    configure_app
    build_war
    setup_tomcat
    deploy_war
    open_firewall
    wait_for_webapp
    check_smtp_network
    status_report
}

main() {
    case "${MODE}" in
        -h|--help|help)
            usage
            exit 0
            ;;
        all|netplan|packages|repo|config|build|tomcat|deploy|status|db-check)
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
            run_all
            ;;
        netplan)
            RUN_NETPLAN=1
            write_netplan
            ;;
        packages)
            install_packages
            ;;
        repo)
            prepare_repo
            ;;
        config)
            configure_app
            ;;
        build)
            build_war
            ;;
        tomcat)
            setup_tomcat
            ;;
        deploy)
            deploy_war
            open_firewall
            wait_for_webapp
            ;;
        status)
            systemctl --no-pager --full status "${SERVICE_NAME}" || true
            check_smtp_network
            status_report
            ;;
        db-check)
            check_db_test_user
            ;;
    esac
}

main "$@"
