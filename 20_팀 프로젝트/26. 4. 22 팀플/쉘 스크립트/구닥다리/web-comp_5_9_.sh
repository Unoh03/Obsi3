#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# =====================================================
# WEB 통합 설치/재구축 스크립트 (5.9)
#
# 목적:
# - WEB1/WEB2 최초 구축 또는 신규 WEB3 투입 시, WEB 서버를 빠르게 서비스 가능한 상태로 만든다.
# - Tomcat 설치, GitHub repo pull/build, ROOT.war 배포, DB/Gmail secret 분리, NFS upload mount, 기본 검증을 한 번에 수행한다.
#
# 실행 위치:
# - 새로 만든 WEB 서버 또는 재구축할 WEB 서버 안에서 실행한다.
# - LB 서버, NFS 서버, DB 서버에서 실행하지 않는다.
#
# 필요한 상태:
# - WEB 서버의 /home/*/zzaphub 또는 PROJECT_DIR 경로에 GitHub repo clone이 있으면 사용한다.
# - repo가 없으면 GIT_URL/GIT_BRANCH 기준으로 자동 clone한다.
# - repo는 WAR + src/main/webapp JSP/CSS/JS + src/main/resources/mappers 구조여야 한다.
# - Promtail은 기본 auto 모드로 WEB 로그를 설정하고, 필요하면 PROMTAIL_MODE=prompt 로 직접 고를 수 있다.
#
# 내장 기능:
# - Tomcat 설치
# - repo pull/build 후 ROOT.war 배포
# - DB/Gmail secret 분리
# - NFS VIP upload mount
#
# 실행 예시:
#   sudo bash 'web-comp_5_9_.sh'
#   sudo PROJECT_DIR=/home/t_web/zzaphub RUN_PROMTAIL=0 bash 'web-comp_5_9_.sh'
#   sudo PROMTAIL_MODE=prompt bash 'web-comp_5_9_.sh'
#
# 자동화/비대화형 실행 예시:
#   sudo MASTER_DB_URL='jdbc:mariadb://1.2.3.1:3306/care' MASTER_DB_USER='web' MASTER_DB_PASSWORD='값은직접입력' \
#        SLAVE_DB_URL='jdbc:mariadb://1.2.3.2:3306/care' SLAVE_DB_USER='web' SLAVE_DB_PASSWORD='값은직접입력' \
#        MAIL_USERNAME='발신용Gmail주소' MAIL_PASSWORD='Gmail앱비밀번호' \
#        bash 'web-comp_5_9_.sh'
#
# 이미 /etc/zzaphub-db.env 가 준비되어 있다면:
#   sudo bash 'web-comp_5_9_.sh'
#
# 중요한 한계:
# - 이 스크립트는 AWS Auto Scaling처럼 VM을 새로 생성하지 않는다.
# - 새 서버 생성, IP 할당, LB upstream 변경은 사람이 하거나 별도 자동화가 해야 한다.
# - 이 스크립트의 목표는 "WEB 서버 안의 표준 세팅을 재현 가능하게 만드는 것"이다.
# =====================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

TOMCAT_VER="${TOMCAT_VER:-10.1.54}"
TOMCAT_BASE_URL="${TOMCAT_BASE_URL:-https://downloads.apache.org/tomcat/tomcat-10}"
TOMCAT_DOWNLOAD_URL="${TOMCAT_DOWNLOAD_URL:-${TOMCAT_BASE_URL}/v${TOMCAT_VER}/bin/apache-tomcat-${TOMCAT_VER}.tar.gz}"
TOMCAT_USER="${TOMCAT_USER:-tomcat}"
TOMCAT_GROUP="${TOMCAT_GROUP:-tomcat}"
TOMCAT_BASE="${TOMCAT_BASE:-/opt/tomcat}"
TOMCAT_HOME="${TOMCAT_HOME:-${TOMCAT_BASE}/tomcat-10}"
SERVICE_NAME="${SERVICE_NAME:-tomcat.service}"
APP_CONTEXT="${APP_CONTEXT:-ROOT}"

PROJECT_DIR="${PROJECT_DIR:-}"
GIT_URL="${GIT_URL:-https://github.com/SUS7898/zzaphub.git}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
BUILT_WAR="${BUILT_WAR:-}"

ENV_FILE="${ENV_FILE:-/etc/zzaphub-db.env}"
PROP_FILE="${PROP_FILE:-${TOMCAT_HOME}/webapps/${APP_CONTEXT}/WEB-INF/classes/application.properties}"
WAR_FILE="${WAR_FILE:-${TOMCAT_HOME}/webapps/${APP_CONTEXT}.war}"
DROPIN_DIR="${DROPIN_DIR:-/etc/systemd/system/${SERVICE_NAME}.d}"
DROPIN_FILE="${DROPIN_FILE:-${DROPIN_DIR}/10-zzaphub-db-env.conf}"
NFS_VIP="${NFS_VIP:-192.168.2.50}"
NFS_VERSION="${NFS_VERSION:-4}"
NFS_REMOTE_SHARE="${NFS_REMOTE_SHARE:-/share_directory}"
MOUNT_DIR="${MOUNT_DIR:-${TOMCAT_HOME}/webapps/upload}"
NFS_BACKUP_BASE="${NFS_BACKUP_BASE:-${TOMCAT_BASE}}"
NFS_EXPECTED_SOURCE="${NFS_VIP}:${NFS_REMOTE_SHARE}"
NFS_FSTAB_OPTIONS="defaults,_netdev,nofail,vers=${NFS_VERSION},proto=tcp,hard,timeo=50,retrans=2,x-systemd.automount,x-systemd.idle-timeout=30s,x-systemd.device-timeout=5s,x-systemd.mount-timeout=10s"
NFS_RUNTIME_OPTIONS="rw,vers=${NFS_VERSION},proto=tcp,hard,timeo=50,retrans=2"
NFS_FSTAB_LINE="${NFS_EXPECTED_SOURCE} ${MOUNT_DIR} nfs ${NFS_FSTAB_OPTIONS} 0 0"
NFS_LOCAL_BACKUP_DIR=""

RUN_SECURE="${RUN_SECURE:-1}"
UPDATE_WAR="${UPDATE_WAR:-1}"
RUN_NFS="${RUN_NFS:-1}"
RUN_PROMTAIL="${RUN_PROMTAIL:-1}"
PROMTAIL_REQUIRED="${PROMTAIL_REQUIRED:-0}"
PROMTAIL_MODE="${PROMTAIL_MODE:-auto}"
PROMTAIL_PRESET="${PROMTAIL_PRESET:-web}"
PROMTAIL_HOST_LABEL="${PROMTAIL_HOST_LABEL:-}"
PROMTAIL_ROLE_LABEL="${PROMTAIL_ROLE_LABEL:-web}"
PROMTAIL_VERSION="${PROMTAIL_VERSION:-2.9.0}"
PROMTAIL_DOWNLOAD_URL="${PROMTAIL_DOWNLOAD_URL:-https://github.com/grafana/loki/releases/download/v${PROMTAIL_VERSION}/promtail-linux-amd64.zip}"
LOKI_PUSH_URL="${LOKI_PUSH_URL:-http://1.2.3.3:3100/loki/api/v1/push}"
PROMTAIL_BIN="${PROMTAIL_BIN:-/usr/local/bin/promtail}"
PROMTAIL_CONFIG="${PROMTAIL_CONFIG:-/etc/promtail/promtail-config.yaml}"
PROMTAIL_SERVICE="${PROMTAIL_SERVICE:-/etc/systemd/system/promtail.service}"
POSITIONS_FILE="${POSITIONS_FILE:-/var/lib/promtail/positions.yaml}"
PROMTAIL_EXTRA_LOGS="${PROMTAIL_EXTRA_LOGS:-}"
INSTALL_NODE_EXPORTER="${INSTALL_NODE_EXPORTER:-1}"
CHECK_LOKI_READY="${CHECK_LOKI_READY:-1}"
ALLOW_UFW="${ALLOW_UFW:-1}"
ALLOW_DIRTY_REPO="${ALLOW_DIRTY_REPO:-0}"
ALLOW_REMOTE_REWRITE="${ALLOW_REMOTE_REWRITE:-0}"

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/zzaphub-web-integrated}"
RUN_ID="$(date +%Y%m%d-%H%M%S)"

EXPECTED_MASTER_DB_URL='${MASTER_DB_URL}'
EXPECTED_MASTER_DB_USER='${MASTER_DB_USER}'
EXPECTED_MASTER_DB_PASSWORD='${MASTER_DB_PASSWORD}'
EXPECTED_SLAVE_DB_URL='${SLAVE_DB_URL}'
EXPECTED_SLAVE_DB_USER='${SLAVE_DB_USER}'
EXPECTED_SLAVE_DB_PASSWORD='${SLAVE_DB_PASSWORD}'
EXPECTED_MAIL_USERNAME='${MAIL_USERNAME}'
EXPECTED_MAIL_PASSWORD='${MAIL_PASSWORD}'

PROMTAIL_JOB_NAMES=()
PROMTAIL_JOB_LABELS=()
PROMTAIL_LOG_PATHS=()

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

require_root() {
    if [ "${EUID}" -ne 0 ]; then
        die "root 권한이 필요합니다. 예: sudo bash '$0'"
    fi
}

backup_path_for() {
    local path="$1"
    local base

    base="$(basename "${path}" | tr -c 'A-Za-z0-9._-' '_')"
    echo "${BACKUP_ROOT}/${base}.${RUN_ID}.bak"
}

backup_file_or_dir() {
    local path="$1"
    local backup_path

    [ -e "${path}" ] || return 0

    install -d -m 700 -o root -g root "${BACKUP_ROOT}"
    backup_path="$(backup_path_for "${path}")"

    if [ -d "${path}" ] && [ ! -L "${path}" ]; then
        cp -a "${path}" "${backup_path}"
    else
        cp -a "${path}" "${backup_path}"
    fi

    chown -R root:root "${backup_path}" 2>/dev/null || true
    chmod -R go-rwx "${backup_path}" 2>/dev/null || true
    echo "${backup_path}"
}

contains_bad_env_chars() {
    local value="$1"

    [[ "${value}" == *$'\n'* ]] || [[ "${value}" == *"'"* ]]
}

get_property() {
    local key="$1"
    local file_path="$2"

    awk -F= -v key="${key}" '
        {
            lhs=$1
            gsub(/^[ \t]+|[ \t]+$/, "", lhs)
            if (lhs == key) {
                sub(/^[^=]*=/, "")
                sub(/\r$/, "")
                print
                exit
            }
        }
    ' "${file_path}"
}

is_placeholder() {
    case "$1" in
        '${MASTER_DB_URL}'|'${MASTER_DB_USER}'|'${MASTER_DB_PASSWORD}'|'${SLAVE_DB_URL}'|'${SLAVE_DB_USER}'|'${SLAVE_DB_PASSWORD}'|'${MAIL_USERNAME}'|'${MAIL_PASSWORD}')
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

quote_env_value() {
    local value="$1"

    if contains_bad_env_chars "${value}"; then
        die "환경파일 값에 작은따옴표 또는 줄바꿈이 있습니다. ${ENV_FILE} 을 직접 작성하세요."
    fi

    printf "'%s'" "${value}"
}

env_has_var() {
    local key="$1"

    [ -f "${ENV_FILE}" ] && grep -Eq "^[[:space:]]*${key}=" "${ENV_FILE}"
}

get_env_file_value() {
    local key="$1"

    [ -f "${ENV_FILE}" ] || return 0

    awk -F= -v key="${key}" '
        {
            lhs=$1
            gsub(/^[ \t]+|[ \t]+$/, "", lhs)
            if (lhs == key) {
                sub(/^[^=]*=/, "")
                sub(/\r$/, "")
                print
                exit
            }
        }
    ' "${ENV_FILE}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e "s/^'//" -e "s/'$//"
}

env_file_var_ready() {
    local key="$1"
    local value

    value="$(get_env_file_value "${key}")"
    [ -n "${value}" ] && ! is_placeholder "${value}"
}

env_file_has_all_db_vars() {
    env_file_var_ready "MASTER_DB_URL" &&
    env_file_var_ready "MASTER_DB_USER" &&
    env_file_var_ready "MASTER_DB_PASSWORD" &&
    env_file_var_ready "SLAVE_DB_URL" &&
    env_file_var_ready "SLAVE_DB_USER" &&
    env_file_var_ready "SLAVE_DB_PASSWORD"
}

env_file_has_all_mail_vars() {
    env_file_var_ready "MAIL_USERNAME" &&
    env_file_var_ready "MAIL_PASSWORD"
}

env_file_has_all_secure_vars() {
    env_file_has_all_db_vars && env_file_has_all_mail_vars
}

append_env_var_if_missing() {
    local env_key="$1"
    local env_value="$2"
    local env_line
    local tmp_file

    if env_file_var_ready "${env_key}"; then
        log "${ENV_FILE} 에 ${env_key} 가 이미 있습니다. 값은 출력하지 않습니다."
        return 0
    fi

    if [ -z "${env_value}" ] || is_placeholder "${env_value}"; then
        return 1
    fi

    env_line="${env_key}=$(quote_env_value "${env_value}")"

    if env_has_var "${env_key}"; then
        warn "${ENV_FILE} 의 ${env_key} 값이 비어 있거나 placeholder라 새 값으로 교체합니다. 값은 출력하지 않습니다."
        tmp_file="$(mktemp)"
        awk -v key="${env_key}" -v line="${env_line}" '
            BEGIN { replaced=0 }
            $0 ~ "^[[:space:]]*" key "=" {
                print line
                replaced=1
                next
            }
            { print }
            END {
                if (replaced == 0) print line
            }
        ' "${ENV_FILE}" > "${tmp_file}"
        cat "${tmp_file}" > "${ENV_FILE}"
        rm -f "${tmp_file}"
    else
        printf '%s\n' "${env_line}" >> "${ENV_FILE}"
    fi

    log "${ENV_FILE} 에 ${env_key} 를 저장했습니다. 값은 출력하지 않습니다."
}

can_prompt_secret_values() {
    [ -t 0 ] && [ -t 1 ]
}

read_required_value() {
    local label="$1"
    local var_name="$2"
    local value

    while true; do
        read -r -p "${label}: " value || return 1
        if [ -n "${value}" ]; then
            printf -v "${var_name}" '%s' "${value}"
            return 0
        fi
        warn "값을 비워둘 수 없습니다: ${label}"
    done
}

read_required_secret_value() {
    local label="$1"
    local var_name="$2"
    local value

    while true; do
        read -r -s -p "${label}: " value || return 1
        echo
        if [ -n "${value}" ]; then
            printf -v "${var_name}" '%s' "${value}"
            return 0
        fi
        warn "값을 비워둘 수 없습니다: ${label}"
    done
}

prompt_env_var_if_needed() {
    local env_key="$1"
    local label="$2"
    local secret="$3"
    local var_name="$4"
    local current_value="${!var_name}"

    if env_file_var_ready "${env_key}"; then
        return 0
    fi

    if env_has_var "${env_key}"; then
        warn "${ENV_FILE} 에 ${env_key} 줄은 있지만 값이 비었거나 placeholder입니다. 새 값이 필요합니다."
    fi

    if [ -n "${current_value}" ] && ! is_placeholder "${current_value}"; then
        return 0
    fi

    if ! can_prompt_secret_values; then
        return 1
    fi

    log "${env_key} 값이 없어 입력이 필요합니다. 값은 로그에 출력하지 않습니다."
    if [ "${secret}" = "1" ]; then
        read_required_secret_value "${label}" "${var_name}"
    else
        read_required_value "${label}" "${var_name}"
    fi
}

print_missing_secret_help() {
    local missing_names="$*"

    warn "대화형 입력이 불가능하거나 필요한 값이 비어 있습니다."
    warn "부족한 값: ${missing_names}"
    warn "방법 1: 터미널에서 sudo bash 'web-comp_5_9_.sh' 로 실행해 질문에 답하세요."
    warn "방법 2: ${ENV_FILE} 을 직접 작성한 뒤 다시 실행하세요."
    cat >&2 <<EOF

${ENV_FILE} 예시:
MASTER_DB_URL='jdbc:mariadb://1.2.3.1:3306/care'
MASTER_DB_USER='web'
MASTER_DB_PASSWORD='DB비밀번호'
SLAVE_DB_URL='jdbc:mariadb://1.2.3.2:3306/care'
SLAVE_DB_USER='web'
SLAVE_DB_PASSWORD='DB비밀번호'
MAIL_USERNAME='발신용Gmail주소'
MAIL_PASSWORD='Gmail앱비밀번호'
EOF
}

ensure_secret_env_file() {
    local master_db_url="${MASTER_DB_URL:-}"
    local master_db_user="${MASTER_DB_USER:-}"
    local master_db_password="${MASTER_DB_PASSWORD:-}"
    local slave_db_url="${SLAVE_DB_URL:-}"
    local slave_db_user="${SLAVE_DB_USER:-}"
    local slave_db_password="${SLAVE_DB_PASSWORD:-}"
    local mail_username="${MAIL_USERNAME:-}"
    local mail_password="${MAIL_PASSWORD:-}"
    local missing=0
    local missing_keys=()

    if env_file_has_all_secure_vars; then
        log "${ENV_FILE} 가 이미 준비되어 있습니다. secret 값은 출력하지 않습니다."
        chmod 600 "${ENV_FILE}" || true
        chown root:root "${ENV_FILE}" 2>/dev/null || true
        return 0
    fi

    if [ -f "${PROP_FILE}" ]; then
        master_db_url="${master_db_url:-$(get_property "spring.datasource.master.jdbc-url" "${PROP_FILE}")}"
        master_db_user="${master_db_user:-$(get_property "spring.datasource.master.username" "${PROP_FILE}")}"
        master_db_password="${master_db_password:-$(get_property "spring.datasource.master.password" "${PROP_FILE}")}"
        slave_db_url="${slave_db_url:-$(get_property "spring.datasource.slave.jdbc-url" "${PROP_FILE}")}"
        slave_db_user="${slave_db_user:-$(get_property "spring.datasource.slave.username" "${PROP_FILE}")}"
        slave_db_password="${slave_db_password:-$(get_property "spring.datasource.slave.password" "${PROP_FILE}")}"
        mail_username="${mail_username:-$(get_property "spring.mail.username" "${PROP_FILE}")}"
        mail_password="${mail_password:-$(get_property "spring.mail.password" "${PROP_FILE}")}"
    fi

    mail_password="${mail_password// /}"

    prompt_env_var_if_needed "MASTER_DB_URL" "MASTER_DB_URL" "0" "master_db_url" || missing_keys+=("MASTER_DB_URL")
    prompt_env_var_if_needed "MASTER_DB_USER" "MASTER_DB_USER" "0" "master_db_user" || missing_keys+=("MASTER_DB_USER")
    prompt_env_var_if_needed "MASTER_DB_PASSWORD" "MASTER_DB_PASSWORD" "1" "master_db_password" || missing_keys+=("MASTER_DB_PASSWORD")
    prompt_env_var_if_needed "SLAVE_DB_URL" "SLAVE_DB_URL" "0" "slave_db_url" || missing_keys+=("SLAVE_DB_URL")
    prompt_env_var_if_needed "SLAVE_DB_USER" "SLAVE_DB_USER" "0" "slave_db_user" || missing_keys+=("SLAVE_DB_USER")
    prompt_env_var_if_needed "SLAVE_DB_PASSWORD" "SLAVE_DB_PASSWORD" "1" "slave_db_password" || missing_keys+=("SLAVE_DB_PASSWORD")
    prompt_env_var_if_needed "MAIL_USERNAME" "MAIL_USERNAME" "0" "mail_username" || missing_keys+=("MAIL_USERNAME")
    prompt_env_var_if_needed "MAIL_PASSWORD" "MAIL_PASSWORD" "1" "mail_password" || missing_keys+=("MAIL_PASSWORD")
    mail_password="${mail_password// /}"

    if [ "${#missing_keys[@]}" -ne 0 ]; then
        print_missing_secret_help "${missing_keys[@]}"
        die "${ENV_FILE} 에 필요한 secret 값을 채울 수 없습니다."
    fi

    install -d -m 755 -o root -g root "$(dirname "${ENV_FILE}")"

    if [ -e "${ENV_FILE}" ]; then
        log "기존 env 파일 백업: $(backup_file_or_dir "${ENV_FILE}")"
    fi

    if [ ! -f "${ENV_FILE}" ]; then
        cat > "${ENV_FILE}" <<EOF
# zzaphub DB and mail secrets
# 이 파일은 Git에 올리지 않는다.
EOF
    fi

    append_env_var_if_missing "MASTER_DB_URL" "${master_db_url}" || missing=1
    append_env_var_if_missing "MASTER_DB_USER" "${master_db_user}" || missing=1
    append_env_var_if_missing "MASTER_DB_PASSWORD" "${master_db_password}" || missing=1
    append_env_var_if_missing "SLAVE_DB_URL" "${slave_db_url}" || missing=1
    append_env_var_if_missing "SLAVE_DB_USER" "${slave_db_user}" || missing=1
    append_env_var_if_missing "SLAVE_DB_PASSWORD" "${slave_db_password}" || missing=1
    append_env_var_if_missing "MAIL_USERNAME" "${mail_username}" || missing=1
    append_env_var_if_missing "MAIL_PASSWORD" "${mail_password}" || missing=1

    chmod 600 "${ENV_FILE}"
    chown root:root "${ENV_FILE}" 2>/dev/null || true

    if [ "${missing}" -ne 0 ]; then
        die "${ENV_FILE} 에 MASTER_DB_*/SLAVE_DB_* 6개와 MAIL_USERNAME/MAIL_PASSWORD 값을 채울 수 없습니다. 환경변수로 넘기거나 파일을 직접 작성하세요."
    fi

    log "${ENV_FILE} 을 생성했습니다. secret 값은 출력하지 않습니다."
}

set_property() {
    local key="$1"
    local value="$2"
    local file_path="$3"
    local tmp_file

    tmp_file="$(mktemp)"

    awk -F= -v key="${key}" -v value="${value}" '
        BEGIN { done = 0 }
        {
            lhs=$1
            gsub(/^[ \t]+|[ \t]+$/, "", lhs)

            if (lhs == key) {
                if (done == 0) {
                    print key "=" value
                    done = 1
                }
                next
            }

            print
        }
        END {
            if (done == 0) {
                print key "=" value
            }
        }
    ' "${file_path}" > "${tmp_file}"

    cat "${tmp_file}" > "${file_path}"
    rm -f "${tmp_file}"
}

properties_already_secure() {
    [ "$(get_property "spring.datasource.master.jdbc-url" "${PROP_FILE}")" = "${EXPECTED_MASTER_DB_URL}" ] &&
    [ "$(get_property "spring.datasource.master.username" "${PROP_FILE}")" = "${EXPECTED_MASTER_DB_USER}" ] &&
    [ "$(get_property "spring.datasource.master.password" "${PROP_FILE}")" = "${EXPECTED_MASTER_DB_PASSWORD}" ] &&
    [ "$(get_property "spring.datasource.slave.jdbc-url" "${PROP_FILE}")" = "${EXPECTED_SLAVE_DB_URL}" ] &&
    [ "$(get_property "spring.datasource.slave.username" "${PROP_FILE}")" = "${EXPECTED_SLAVE_DB_USER}" ] &&
    [ "$(get_property "spring.datasource.slave.password" "${PROP_FILE}")" = "${EXPECTED_SLAVE_DB_PASSWORD}" ] &&
    [ "$(get_property "spring.mail.username" "${PROP_FILE}")" = "${EXPECTED_MAIL_USERNAME}" ] &&
    [ "$(get_property "spring.mail.password" "${PROP_FILE}")" = "${EXPECTED_MAIL_PASSWORD}" ]
}

mail_transport_already_configured() {
    [ "$(get_property "spring.mail.host" "${PROP_FILE}")" = "smtp.gmail.com" ] &&
    [ "$(get_property "spring.mail.port" "${PROP_FILE}")" = "587" ] &&
    [ "$(get_property "spring.mail.properties.mail.smtp.auth" "${PROP_FILE}")" = "true" ] &&
    [ "$(get_property "spring.mail.properties.mail.smtp.starttls.enable" "${PROP_FILE}")" = "true" ] &&
    [ "$(get_property "spring.mail.properties.mail.smtp.starttls.required" "${PROP_FILE}")" = "true" ]
}

ensure_mail_transport_properties() {
    set_property "spring.mail.host" "smtp.gmail.com" "${PROP_FILE}"
    set_property "spring.mail.port" "587" "${PROP_FILE}"
    set_property "spring.mail.properties.mail.smtp.auth" "true" "${PROP_FILE}"
    set_property "spring.mail.properties.mail.smtp.starttls.enable" "true" "${PROP_FILE}"
    set_property "spring.mail.properties.mail.smtp.starttls.required" "true" "${PROP_FILE}"
}

secure_application_properties() {
    local properties_secure=0
    local mail_transport_ready=0

    if properties_already_secure; then
        properties_secure=1
    fi

    if mail_transport_already_configured; then
        mail_transport_ready=1
    fi

    if [ "${properties_secure}" -eq 1 ] && [ "${mail_transport_ready}" -eq 1 ]; then
        log "application.properties 는 이미 DB/Gmail 환경변수 placeholder 와 Gmail SMTP 설정을 사용합니다."
        return 0
    fi

    log "application.properties 백업: $(backup_file_or_dir "${PROP_FILE}")"

    if [ "${properties_secure}" -ne 1 ]; then
        set_property "spring.datasource.master.jdbc-url" "${EXPECTED_MASTER_DB_URL}" "${PROP_FILE}"
        set_property "spring.datasource.master.username" "${EXPECTED_MASTER_DB_USER}" "${PROP_FILE}"
        set_property "spring.datasource.master.password" "${EXPECTED_MASTER_DB_PASSWORD}" "${PROP_FILE}"
        set_property "spring.datasource.slave.jdbc-url" "${EXPECTED_SLAVE_DB_URL}" "${PROP_FILE}"
        set_property "spring.datasource.slave.username" "${EXPECTED_SLAVE_DB_USER}" "${PROP_FILE}"
        set_property "spring.datasource.slave.password" "${EXPECTED_SLAVE_DB_PASSWORD}" "${PROP_FILE}"
        set_property "spring.mail.username" "${EXPECTED_MAIL_USERNAME}" "${PROP_FILE}"
        set_property "spring.mail.password" "${EXPECTED_MAIL_PASSWORD}" "${PROP_FILE}"
        log "application.properties 의 master/slave DB 접속정보와 Gmail 발신 계정을 환경변수 placeholder 로 변경했습니다."
    fi

    if [ "${mail_transport_ready}" -ne 1 ]; then
        ensure_mail_transport_properties
        log "application.properties 의 Gmail SMTP 기본 설정을 보정했습니다."
    fi
}

write_systemd_dropin() {
    install -d -m 755 -o root -g root "${DROPIN_DIR}"

    if [ -f "${DROPIN_FILE}" ] && grep -Fq "EnvironmentFile=${ENV_FILE}" "${DROPIN_FILE}"; then
        log "systemd drop-in 이 이미 ${ENV_FILE} 을 참조합니다."
        return 0
    fi

    if [ -f "${DROPIN_FILE}" ]; then
        log "기존 systemd drop-in 백업: $(backup_file_or_dir "${DROPIN_FILE}")"
    fi

    cat > "${DROPIN_FILE}" <<EOF
[Service]
EnvironmentFile=${ENV_FILE}
EOF
    chmod 644 "${DROPIN_FILE}"

    log "Tomcat systemd drop-in 작성: ${DROPIN_FILE}"
}

cleanup_tmp_dir() {
    local tmp_dir="$1"

    case "${tmp_dir}" in
        /tmp/*|/var/tmp/*)
            rm -rf -- "${tmp_dir}"
            ;;
        *)
            warn "임시 디렉터리 경로가 예상 밖이라 삭제하지 않습니다: ${tmp_dir}"
            ;;
    esac
}

update_war_if_present() {
    local tmp_dir

    if [ "${UPDATE_WAR}" != "1" ]; then
        warn "UPDATE_WAR=0 이므로 배포 WAR 내부 properties 갱신을 건너뜁니다."
        return 0
    fi

    if [ ! -f "${WAR_FILE}" ]; then
        warn "${WAR_FILE} 이 없습니다. 배포된 폴더만 수정했습니다."
        return 0
    fi

    if ! command -v jar >/dev/null 2>&1; then
        warn "jar 명령을 찾을 수 없어 ${WAR_FILE} 갱신을 건너뜁니다."
        return 0
    fi

    log "배포 WAR 백업: $(backup_file_or_dir "${WAR_FILE}")"

    tmp_dir="$(mktemp -d)"
    mkdir -p "${tmp_dir}/WEB-INF/classes"
    cp "${PROP_FILE}" "${tmp_dir}/WEB-INF/classes/application.properties"

    (
        cd "${tmp_dir}"
        jar uf "${WAR_FILE}" WEB-INF/classes/application.properties
    )

    cleanup_tmp_dir "${tmp_dir}"
    log "배포 WAR 내부 application.properties 도 placeholder 버전으로 갱신했습니다."
}

restart_tomcat_after_secure_patch() {
    systemctl daemon-reload
    systemctl restart "${SERVICE_NAME}"
    log "Tomcat 재시작 완료: ${SERVICE_NAME}"
}

verify_secure_patch() {
    local failed=0

    [ "$(get_property "spring.datasource.master.jdbc-url" "${PROP_FILE}")" = "${EXPECTED_MASTER_DB_URL}" ] || failed=1
    [ "$(get_property "spring.datasource.master.username" "${PROP_FILE}")" = "${EXPECTED_MASTER_DB_USER}" ] || failed=1
    [ "$(get_property "spring.datasource.master.password" "${PROP_FILE}")" = "${EXPECTED_MASTER_DB_PASSWORD}" ] || failed=1
    [ "$(get_property "spring.datasource.slave.jdbc-url" "${PROP_FILE}")" = "${EXPECTED_SLAVE_DB_URL}" ] || failed=1
    [ "$(get_property "spring.datasource.slave.username" "${PROP_FILE}")" = "${EXPECTED_SLAVE_DB_USER}" ] || failed=1
    [ "$(get_property "spring.datasource.slave.password" "${PROP_FILE}")" = "${EXPECTED_SLAVE_DB_PASSWORD}" ] || failed=1
    [ "$(get_property "spring.mail.username" "${PROP_FILE}")" = "${EXPECTED_MAIL_USERNAME}" ] || failed=1
    [ "$(get_property "spring.mail.password" "${PROP_FILE}")" = "${EXPECTED_MAIL_PASSWORD}" ] || failed=1
    [ "$(get_property "spring.mail.host" "${PROP_FILE}")" = "smtp.gmail.com" ] || failed=1
    [ "$(get_property "spring.mail.port" "${PROP_FILE}")" = "587" ] || failed=1
    [ "$(get_property "spring.mail.properties.mail.smtp.auth" "${PROP_FILE}")" = "true" ] || failed=1
    [ "$(get_property "spring.mail.properties.mail.smtp.starttls.enable" "${PROP_FILE}")" = "true" ] || failed=1
    [ "$(get_property "spring.mail.properties.mail.smtp.starttls.required" "${PROP_FILE}")" = "true" ] || failed=1
    env_file_has_all_secure_vars || failed=1
    [ -f "${DROPIN_FILE}" ] && grep -Fq "EnvironmentFile=${ENV_FILE}" "${DROPIN_FILE}" || failed=1

    if [ "${failed}" -ne 0 ]; then
        die "DB/Gmail secret 내장 통합 검증 실패"
    fi

    log "DB/Gmail secret 분리 검증 완료"
}

install_packages() {
    log "필수 패키지를 설치합니다."
    apt update
    apt install -y openjdk-17-jdk curl wget tar
}

ensure_build_tools() {
    log "Git/Maven 빌드 도구를 설치합니다."
    apt install -y git maven
}

resolve_project_dir() {
    local candidate
    local candidates=()
    local home_dirs=()

    if [ -n "${PROJECT_DIR}" ]; then
        return 0
    fi

    for candidate in /home/*/zzaphub; do
        [ -d "${candidate}/.git" ] || continue
        candidates+=("${candidate}")
    done

    case "${#candidates[@]}" in
        0)
            ;;
        1)
            PROJECT_DIR="${candidates[0]}"
            return 0
            ;;
        *)
            warn "zzaphub repo 후보가 여러 개입니다:"
            printf '  %s\n' "${candidates[@]}" >&2
            die "PROJECT_DIR=/home/사용자/zzaphub 를 지정하세요."
            ;;
    esac

    if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ] && [ -d "/home/${SUDO_USER}" ]; then
        PROJECT_DIR="/home/${SUDO_USER}/zzaphub"
        return 0
    fi

    mapfile -t home_dirs < <(find /home -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort || true)
    case "${#home_dirs[@]}" in
        1)
            PROJECT_DIR="${home_dirs[0]}/zzaphub"
            ;;
        *)
            die "/home/*/zzaphub Git repo를 찾지 못했고 기본 clone 위치도 고를 수 없습니다. PROJECT_DIR=/home/사용자/zzaphub 를 지정하세요."
            ;;
    esac
}

run_in_project_dir() {
    local owner

    owner="$(stat -c '%U' "${PROJECT_DIR}" 2>/dev/null || echo root)"

    if [ "${owner}" != "root" ] && command -v sudo >/dev/null 2>&1; then
        sudo -u "${owner}" -H bash -c 'cd "$1" && shift && "$@"' bash "${PROJECT_DIR}" "$@"
    else
        (
            cd "${PROJECT_DIR}"
            "$@"
        )
    fi
}

dir_is_empty() {
    local path="$1"

    [ -d "${path}" ] && [ -z "$(find "${path}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]
}

path_owner() {
    local path="$1"
    local parent

    if [ -e "${path}" ]; then
        stat -c '%U' "${path}" 2>/dev/null || echo root
        return 0
    fi

    parent="$(dirname "${path}")"
    stat -c '%U' "${parent}" 2>/dev/null || echo root
}

run_as_owner() {
    local owner="$1"
    shift

    if [ "${owner}" != "root" ] && command -v sudo >/dev/null 2>&1; then
        sudo -u "${owner}" -H "$@"
    else
        "$@"
    fi
}

clone_source_repo() {
    local parent
    local owner

    parent="$(dirname "${PROJECT_DIR}")"
    mkdir -p "${parent}"

    if [ -e "${PROJECT_DIR}" ] && [ ! -d "${PROJECT_DIR}" ]; then
        die "PROJECT_DIR 경로가 디렉터리가 아닙니다: ${PROJECT_DIR}"
    fi

    if [ -d "${PROJECT_DIR}" ] && ! dir_is_empty "${PROJECT_DIR}"; then
        die "PROJECT_DIR 이 비어 있지 않고 Git repo도 아닙니다: ${PROJECT_DIR}"
    fi

    owner="$(path_owner "${PROJECT_DIR}")"
    log "zzaphub repo를 clone합니다: ${GIT_URL} (${GIT_BRANCH}) -> ${PROJECT_DIR}"
    run_as_owner "${owner}" git clone --branch "${GIT_BRANCH}" "${GIT_URL}" "${PROJECT_DIR}"
}

ensure_source_repo() {
    if [ -d "${PROJECT_DIR}/.git" ]; then
        return 0
    fi

    clone_source_repo

    [ -d "${PROJECT_DIR}/.git" ] || die "git clone 이후에도 Git repo를 찾지 못했습니다: ${PROJECT_DIR}"
}

ensure_repo_remote() {
    local remote_url

    remote_url="$(run_in_project_dir git config --get "remote.${GIT_REMOTE}.url" 2>/dev/null || true)"

    if [ -z "${remote_url}" ]; then
        log "Git remote ${GIT_REMOTE} 이 없어 추가합니다: ${GIT_URL}"
        run_in_project_dir git remote add "${GIT_REMOTE}" "${GIT_URL}"
        return 0
    fi

    if [ "${remote_url}" = "${GIT_URL}" ]; then
        return 0
    fi

    if [ "${ALLOW_REMOTE_REWRITE}" = "1" ]; then
        warn "Git remote ${GIT_REMOTE} URL을 변경합니다: ${remote_url} -> ${GIT_URL}"
        run_in_project_dir git remote set-url "${GIT_REMOTE}" "${GIT_URL}"
        return 0
    fi

    die "Git remote ${GIT_REMOTE} URL이 기대값과 다릅니다. 현재: ${remote_url}, 기대: ${GIT_URL}. 필요하면 ALLOW_REMOTE_REWRITE=1 로 실행하세요."
}

ensure_repo_clean_if_needed() {
    local dirty

    dirty="$(run_in_project_dir git status --porcelain)"
    if [ -z "${dirty}" ]; then
        return 0
    fi

    if [ "${ALLOW_DIRTY_REPO}" = "1" ]; then
        warn "Git worktree에 변경이 있지만 ALLOW_DIRTY_REPO=1 이므로 계속 진행합니다."
        return 0
    fi

    warn "Git worktree에 commit되지 않은 변경이 있습니다:"
    printf '%s\n' "${dirty}" >&2
    die "기존 작업을 덮지 않기 위해 중단합니다. 정리 후 재실행하거나 테스트용이면 ALLOW_DIRTY_REPO=1 로 실행하세요."
}

ensure_repo_branch() {
    local current_branch

    current_branch="$(run_in_project_dir git branch --show-current 2>/dev/null || true)"
    if [ "${current_branch}" = "${GIT_BRANCH}" ]; then
        return 0
    fi

    log "Git branch를 ${GIT_BRANCH} 로 맞춥니다. 현재: ${current_branch:-detached}"
    run_in_project_dir git fetch "${GIT_REMOTE}"

    if run_in_project_dir git show-ref --verify --quiet "refs/heads/${GIT_BRANCH}"; then
        run_in_project_dir git switch "${GIT_BRANCH}"
        return 0
    fi

    if run_in_project_dir git show-ref --verify --quiet "refs/remotes/${GIT_REMOTE}/${GIT_BRANCH}"; then
        run_in_project_dir git switch --track -c "${GIT_BRANCH}" "${GIT_REMOTE}/${GIT_BRANCH}"
        return 0
    fi

    die "Git branch를 찾지 못했습니다: ${GIT_REMOTE}/${GIT_BRANCH}"
}

prepare_source_repo() {
    resolve_project_dir
    log "소스 repo 경로: ${PROJECT_DIR}"
    ensure_source_repo
    ensure_repo_remote
    ensure_repo_clean_if_needed
    ensure_repo_branch
    log "Git 최신 코드 반영: ${GIT_REMOTE} ${GIT_BRANCH}"
    run_in_project_dir git pull --ff-only "${GIT_REMOTE}" "${GIT_BRANCH}"
}

normalize_application_properties_location() {
    local resource_dir="${PROJECT_DIR}/src/main/resources"
    local java_prop="${PROJECT_DIR}/src/main/java/application.properties"
    local resource_prop="${resource_dir}/application.properties"
    local chown_ref="${PROJECT_DIR}/src/main"

    if [ ! -d "${resource_dir}" ]; then
        mkdir -p "${resource_dir}"
        [ -e "${chown_ref}" ] || chown_ref="${PROJECT_DIR}"
        chown --reference="${chown_ref}" "${resource_dir}" 2>/dev/null || true
    fi

    if [ -f "${resource_prop}" ] && [ -f "${java_prop}" ]; then
        log "src/main/resources/application.properties 를 우선 사용합니다."
        log "src/main/java/application.properties 백업: $(backup_file_or_dir "${java_prop}")"
        rm -f -- "${java_prop}"
        return 0
    fi

    if [ ! -f "${resource_prop}" ] && [ -f "${java_prop}" ]; then
        log "application.properties 를 src/main/java 에서 src/main/resources 로 이동합니다."
        log "이동 전 백업: $(backup_file_or_dir "${java_prop}")"
        mv "${java_prop}" "${resource_prop}"
        return 0
    fi
}

validate_repo_layout() {
    local resource_dir="${PROJECT_DIR}/src/main/resources"
    local webapp_dir="${PROJECT_DIR}/src/main/webapp"

    [ -f "${resource_dir}/application.properties" ] ||
        die "${resource_dir}/application.properties 가 없습니다. application.properties는 src/main/resources 아래에 있어야 합니다."

    [ -d "${resource_dir}/mappers" ] ||
        die "${resource_dir}/mappers 디렉터리가 없습니다. MyBatis mapper XML은 src/main/resources/mappers 아래에 있어야 합니다."

    [ -d "${webapp_dir}" ] ||
        die "${webapp_dir} 디렉터리가 없습니다. 현재 zzaphub는 WAR + src/main/webapp 구조여야 합니다."

    [ -d "${webapp_dir}/jsp" ] ||
        die "${webapp_dir}/jsp 디렉터리가 없습니다. JSP 화면 누락 배포를 막기 위해 중단합니다."

    [ -d "${webapp_dir}/css" ] ||
        die "${webapp_dir}/css 디렉터리가 없습니다. CSS 누락 배포를 막기 위해 중단합니다."

    [ -d "${webapp_dir}/js" ] ||
        die "${webapp_dir}/js 디렉터리가 없습니다. JS 누락 배포를 막기 위해 중단합니다."
}

build_war_from_repo() {
    local wars=()

    if [ -n "${BUILT_WAR}" ]; then
        [ -f "${BUILT_WAR}" ] || die "BUILT_WAR 파일을 찾을 수 없습니다: ${BUILT_WAR}"
        log "외부 지정 WAR를 사용합니다: ${BUILT_WAR}"
        return 0
    fi

    log "Maven 빌드를 실행합니다: mvn clean package -DskipTests"
    run_in_project_dir mvn clean package -DskipTests

    mapfile -t wars < <(find "${PROJECT_DIR}/target" -maxdepth 1 -type f -name '*.war' | sort)

    case "${#wars[@]}" in
        1)
            BUILT_WAR="${wars[0]}"
            log "빌드된 WAR 확인: ${BUILT_WAR}"
            ;;
        0)
            die "${PROJECT_DIR}/target 에 WAR 파일이 없습니다. 빌드 로그를 확인하거나 BUILT_WAR=/path/app.war 를 지정하세요."
            ;;
        *)
            warn "WAR 파일이 여러 개입니다:"
            printf '  %s\n' "${wars[@]}" >&2
            die "배포할 WAR를 BUILT_WAR=/path/app.war 로 지정하세요."
            ;;
    esac
}

ensure_tomcat_user() {
    if id "${TOMCAT_USER}" >/dev/null 2>&1; then
        log "${TOMCAT_USER} 계정이 이미 있습니다."
        return 0
    fi

    log "${TOMCAT_USER} 전용 계정을 생성합니다."
    useradd -r -m -U -d "${TOMCAT_BASE}" -s /bin/false "${TOMCAT_USER}"
}

install_tomcat_if_needed() {
    local tarball
    local tmp_dir
    local extracted_dir

    if [ -x "${TOMCAT_HOME}/bin/startup.sh" ]; then
        log "Tomcat이 이미 설치되어 있습니다: ${TOMCAT_HOME}"
        return 0
    fi

    if [ -e "${TOMCAT_HOME}" ]; then
        die "${TOMCAT_HOME} 이 이미 있지만 Tomcat 설치로 보이지 않습니다. 수동 확인 후 정리하세요."
    fi

    log "Tomcat ${TOMCAT_VER} 를 설치합니다."
    install -d -m 755 -o "${TOMCAT_USER}" -g "${TOMCAT_GROUP}" "${TOMCAT_BASE}"

    tmp_dir="$(mktemp -d)"
    tarball="${tmp_dir}/apache-tomcat-${TOMCAT_VER}.tar.gz"
    extracted_dir="${TOMCAT_BASE}/apache-tomcat-${TOMCAT_VER}"

    log "Tomcat download URL: ${TOMCAT_DOWNLOAD_URL}"
    wget -O "${tarball}" "${TOMCAT_DOWNLOAD_URL}"
    tar -xf "${tarball}" -C "${TOMCAT_BASE}"
    mv "${extracted_dir}" "${TOMCAT_HOME}"
    chown -R "${TOMCAT_USER}:${TOMCAT_GROUP}" "${TOMCAT_HOME}"
    rm -rf -- "${tmp_dir}"
}

write_tomcat_service() {
    local service_file="/etc/systemd/system/${SERVICE_NAME}"

    if [ -f "${service_file}" ]; then
        log "기존 ${SERVICE_NAME} 백업: $(backup_file_or_dir "${service_file}")"
    fi

    log "${SERVICE_NAME} systemd 서비스를 작성합니다."
    cat > "${service_file}" <<EOF
[Unit]
Description=Tomcat 10 servlet container
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
User=${TOMCAT_USER}
Group=${TOMCAT_GROUP}
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

backup_and_remove_deploy_path() {
    local path="$1"

    [ -e "${path}" ] || return 0

    case "${path}" in
        "${TOMCAT_HOME}/webapps/"*)
            ;;
        *)
            die "배포물 삭제 대상 경로가 예상 범위를 벗어났습니다: ${path}"
            ;;
    esac

    log "기존 배포물 백업: $(backup_file_or_dir "${path}")"
    rm -rf -- "${path}"
}

clear_tomcat_work_cache() {
    local work_dir="${TOMCAT_HOME}/work/Catalina/localhost"

    if [ -d "${work_dir}" ]; then
        log "Tomcat work cache 정리: ${work_dir}"
        find "${work_dir}" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
    fi
}

deploy_built_war_as_ROOT() {
    local target_war="${WAR_FILE}"
    local deploy_names=(ROOT ROOT.war zzaphub zzaphub.war boot boot.war)
    local name

    [ -f "${BUILT_WAR}" ] || die "배포할 WAR 파일을 찾을 수 없습니다: ${BUILT_WAR}"

    systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
    install -d -m 755 -o "${TOMCAT_USER}" -g "${TOMCAT_GROUP}" "${TOMCAT_HOME}/webapps"

    for name in "${deploy_names[@]}"; do
        backup_and_remove_deploy_path "${TOMCAT_HOME}/webapps/${name}"
    done

    clear_tomcat_work_cache

    log "빌드된 WAR를 ${APP_CONTEXT}.war 로 배포합니다: ${target_war}"
    cp "${BUILT_WAR}" "${target_war}"
    chown "${TOMCAT_USER}:${TOMCAT_GROUP}" "${target_war}"

    systemctl start "${SERVICE_NAME}"
}

wait_for_app_properties() {
    local prop_file="${TOMCAT_HOME}/webapps/${APP_CONTEXT}/WEB-INF/classes/application.properties"
    local waited=0
    local max_wait="${APP_EXPAND_WAIT:-60}"

    log "Tomcat이 WAR를 풀 때까지 기다립니다: ${prop_file}"

    while ! test -f "${prop_file}"; do
        sleep 1
        waited=$((waited + 1))
        echo "[INFO] application.properties 대기 중... (${waited}/${max_wait}s)"

        if [ "${waited}" -ge "${max_wait}" ]; then
            die "${prop_file} 을 찾지 못했습니다. Tomcat 로그를 확인하세요: journalctl -u ${SERVICE_NAME} -n 100 --no-pager"
        fi
    done
}

run_secure_patch() {
    if [ "${RUN_SECURE}" != "1" ]; then
        warn "RUN_SECURE=0 이므로 DB/Gmail secret 분리를 건너뜁니다."
        return 0
    fi

    [ -f "${PROP_FILE}" ] || die "${PROP_FILE} 을 찾을 수 없습니다. Tomcat이 WAR를 아직 풀지 않았거나 APP_CONTEXT/TOMCAT_HOME 이 다릅니다."
    ensure_secret_env_file
    secure_application_properties
    write_systemd_dropin
    update_war_if_present
    restart_tomcat_after_secure_patch
    verify_secure_patch
}

nfs_mount_sources() {
    findmnt -n -o SOURCE --mountpoint "${MOUNT_DIR}" 2>/dev/null | sed '/^[[:space:]]*$/d' || true
}

nfs_mount_source_count() {
    nfs_mount_sources | wc -l
}

nfs_current_mount_source() {
    nfs_mount_sources | head -n 1
}

nfs_is_mounted() {
    [ "$(nfs_mount_source_count)" -gt 0 ]
}

nfs_is_expected_source() {
    [ "$1" = "${NFS_EXPECTED_SOURCE}" ] || [ "$1" = "${NFS_EXPECTED_SOURCE}/" ]
}

print_nfs_mount_status() {
    log "NFS mount status:"
    findmnt --mountpoint "${MOUNT_DIR}" || true
    df -h | grep "${MOUNT_DIR}" || true
    mount | grep "${MOUNT_DIR}" || true
}

print_nfs_mount_debug() {
    echo "[DEBUG] fstab entries for this mount point:"
    grep -n "${MOUNT_DIR}" /etc/fstab || true
    echo "[DEBUG] findmnt:"
    findmnt --mountpoint "${MOUNT_DIR}" || true
    echo "[DEBUG] mount output:"
    mount | grep -E "${NFS_VIP}|${NFS_REMOTE_SHARE}|${MOUNT_DIR}" || true
    echo "[DEBUG] /proc/mounts:"
    grep -E "${NFS_VIP}|${NFS_REMOTE_SHARE}|${MOUNT_DIR}" /proc/mounts || true
}

register_nfs_fstab() {
    log "NFS VIP mount를 /etc/fstab에 등록합니다."
    sed -i "\|[[:space:]]${MOUNT_DIR}[[:space:]]|d" /etc/fstab
    echo "${NFS_FSTAB_LINE}" >> /etc/fstab
    systemctl daemon-reload
}

remount_current_nfs_mount() {
    log "기존 NFS mount 옵션 갱신을 시도합니다."
    if timeout 20s mount -o "remount,${NFS_RUNTIME_OPTIONS}" "${MOUNT_DIR}"; then
        log "NFS remount 완료"
    else
        warn "NFS remount 실패 또는 timeout. fstab은 갱신되었고 reboot/remount 때 적용될 수 있습니다."
    fi
}

prepare_nfs_mount_point_and_backup() {
    NFS_LOCAL_BACKUP_DIR=""
    install -d -m 755 "${MOUNT_DIR}"

    if find "${MOUNT_DIR}" -mindepth 1 -print -quit | grep -q .; then
        NFS_LOCAL_BACKUP_DIR="${NFS_BACKUP_BASE}/upload-local-backup-$(date +%Y%m%d-%H%M%S)"
        log "기존 로컬 upload 파일을 NFS mount 전에 백업합니다: ${NFS_LOCAL_BACKUP_DIR}"
        mkdir -p "${NFS_LOCAL_BACKUP_DIR}"
        cp -a "${MOUNT_DIR}/." "${NFS_LOCAL_BACKUP_DIR}/"
    else
        log "기존 로컬 upload 파일이 없습니다."
    fi
}

copy_backup_without_overwrite() {
    local source_dir="$1"
    local target_dir="$2"

    if cp --help 2>/dev/null | grep -q -- '--update='; then
        cp -r --update=none "${source_dir}/." "${target_dir}/"
    else
        cp -rn "${source_dir}/." "${target_dir}/"
    fi
}

apply_nfs_mount() {
    local backup_dir="${NFS_LOCAL_BACKUP_DIR:-}"

    register_nfs_fstab

    if [[ "${NFS_VERSION}" = 4* ]]; then
        log "NFSv${NFS_VERSION}/TCP mode: showmount 확인을 건너뛰고 직접 mount합니다."
    else
        showmount -e "${NFS_VIP}" || warn "showmount 실패. 그래도 직접 NFS mount를 시도합니다."
    fi

    if timeout 20s mount -v -t nfs -o "${NFS_RUNTIME_OPTIONS}" "${NFS_EXPECTED_SOURCE}" "${MOUNT_DIR}"; then
        log "NFS 직접 mount 명령 완료"
    else
        print_nfs_mount_debug
        die "NFS 직접 mount 실패"
    fi

    if ! nfs_is_mounted; then
        print_nfs_mount_debug
        die "${MOUNT_DIR} 가 mount되지 않았습니다."
    fi

    if [ "$(nfs_mount_source_count)" -gt 1 ]; then
        print_nfs_mount_debug
        die "${MOUNT_DIR} 에 중복 mount가 감지되었습니다. 수동 umount 후 다시 실행하세요."
    fi

    if ! nfs_is_expected_source "$(nfs_current_mount_source)"; then
        print_nfs_mount_debug
        die "${MOUNT_DIR} mount source가 기대값과 다릅니다. 기대값: ${NFS_EXPECTED_SOURCE}"
    fi

    if [ -n "${backup_dir}" ]; then
        log "백업했던 로컬 upload 파일을 NFS로 복사합니다. 같은 이름은 덮어쓰지 않습니다."
        copy_backup_without_overwrite "${backup_dir}" "${MOUNT_DIR}"
        log "로컬 백업은 유지됩니다: ${backup_dir}"
    fi
}

install_nfs_packages() {
    if [ "${RUN_NFS}" != "1" ]; then
        return 0
    fi

    log "NFS 클라이언트 패키지를 설치합니다. (인터넷 필요)"
    apt install -y nfs-common lsof
}

run_nfs_mount() {
    local mount_count
    local current_source

    if [ "${RUN_NFS}" != "1" ]; then
        warn "RUN_NFS=0 이므로 NFS upload mount를 건너뜁니다."
        return 0
    fi

    log "내장 NFS VIP upload mount를 시작합니다."
    log "NFS source=${NFS_EXPECTED_SOURCE}, mount=${MOUNT_DIR}"

    install -d -m 755 "${MOUNT_DIR}"

    if nfs_is_mounted; then
        mount_count="$(nfs_mount_source_count)"
        if [ "${mount_count}" -gt 1 ]; then
            print_nfs_mount_debug
            die "${MOUNT_DIR} 에 중복 mount가 있습니다. sudo umount ${MOUNT_DIR} 후 다시 실행하세요."
        fi

        current_source="$(nfs_current_mount_source)"
        if nfs_is_expected_source "${current_source}"; then
            log "${MOUNT_DIR} 는 이미 정상 NFS VIP source에서 mount되어 있습니다: ${current_source}"
            register_nfs_fstab
            remount_current_nfs_mount
            print_nfs_mount_status
            return 0
        fi

        print_nfs_mount_debug
        die "${MOUNT_DIR} 가 예상과 다른 source에서 mount되어 있습니다. 현재: ${current_source:-unknown}, 기대: ${NFS_EXPECTED_SOURCE}"
    fi

    prepare_nfs_mount_point_and_backup
    apply_nfs_mount
    print_nfs_mount_status
}

promtail_service_name() {
    local service_name

    service_name="$(basename "${PROMTAIL_SERVICE}")"
    printf '%s' "${service_name%.service}"
}

promtail_default_host_label() {
    hostname -s 2>/dev/null || hostname 2>/dev/null || echo web
}

promtail_validate_label_value() {
    local name="$1"
    local value="$2"

    case "${value}" in
        *\"*|*$'\n'*|*$'\r'*|"")
            die "${name} 값에는 큰따옴표, 줄바꿈, 빈 값을 넣을 수 없습니다: ${value}"
            ;;
    esac
}

promtail_validate_job_name() {
    local value="$1"

    case "${value}" in
        *[!A-Za-z0-9._-]*|"")
            die "Promtail job_name은 영문/숫자/점/밑줄/하이픈만 사용합니다. 현재 값: ${value}"
            ;;
    esac
}

promtail_validate_loki_push_url() {
    case "$1" in
        http://*/loki/api/v1/push|https://*/loki/api/v1/push)
            ;;
        *)
            die "Loki push URL 형식이 이상합니다: $1"
            ;;
    esac
}

promtail_loki_ready_url() {
    printf '%s' "${LOKI_PUSH_URL%/loki/api/v1/push}/ready"
}

promtail_reset_jobs() {
    PROMTAIL_JOB_NAMES=()
    PROMTAIL_JOB_LABELS=()
    PROMTAIL_LOG_PATHS=()
}

promtail_add_job() {
    local job_name="$1"
    local job_label="$2"
    local log_path="$3"

    promtail_validate_job_name "${job_name}"
    promtail_validate_label_value "job label" "${job_label}"
    promtail_validate_label_value "log path" "${log_path}"

    PROMTAIL_JOB_NAMES+=("${job_name}")
    PROMTAIL_JOB_LABELS+=("${job_label}")
    PROMTAIL_LOG_PATHS+=("${log_path}")
}

promtail_add_common_system_logs() {
    promtail_add_job "system" "varlogs" "/var/log/*.log"
    promtail_add_job "syslog" "syslog" "/var/log/syslog"
}

promtail_add_extra_logs() {
    local spec_string="$1"
    local old_ifs="$IFS"
    local spec
    local job_name
    local job_label
    local log_path

    IFS=';'
    for spec in ${spec_string}; do
        IFS="${old_ifs}"
        [ -n "${spec}" ] || continue

        job_name="${spec%%:*}"
        spec="${spec#*:}"
        job_label="${spec%%:*}"
        log_path="${spec#*:}"

        if [ -z "${job_name}" ] || [ -z "${job_label}" ] || [ -z "${log_path}" ] || [ "${job_label}" = "${log_path}" ]; then
            die "PROMTAIL_EXTRA_LOGS 형식은 job_name:job_label:/path/*.log;... 입니다."
        fi

        promtail_add_job "${job_name}" "${job_label}" "${log_path}"
        IFS=';'
    done
    IFS="${old_ifs}"
}

promtail_collect_auto_jobs() {
    case "${PROMTAIL_PRESET}" in
        web)
            promtail_add_common_system_logs
            promtail_add_job "tomcat" "tomcat-log" "${TOMCAT_HOME}/logs/*.log"
            promtail_add_job "tomcat_out" "tomcat-out" "${TOMCAT_HOME}/logs/catalina.out"
            ;;
        lb)
            promtail_add_common_system_logs
            promtail_add_job "nginx" "nginx-log" "/var/log/nginx/*.log"
            ;;
        dns)
            promtail_add_common_system_logs
            promtail_add_job "bind" "dns-log" "/var/log/bind/*.log"
            promtail_add_job "named" "named-log" "/var/log/named/*.log"
            ;;
        db)
            promtail_add_common_system_logs
            promtail_add_job "mysql" "mysql-log" "/var/log/mysql/*.log"
            promtail_add_job "mariadb" "mariadb-log" "/var/log/mysql/error.log"
            ;;
        nfs)
            promtail_add_common_system_logs
            promtail_add_job "nfs_ha_sync" "nfs-ha-sync" "/var/log/nfs-ha-sync.log"
            ;;
        system)
            promtail_add_common_system_logs
            ;;
        *)
            die "지원하지 않는 PROMTAIL_PRESET입니다: ${PROMTAIL_PRESET}"
            ;;
    esac

    if [ -n "${PROMTAIL_EXTRA_LOGS}" ]; then
        promtail_add_extra_logs "${PROMTAIL_EXTRA_LOGS}"
    fi
}

promtail_read_value() {
    local prompt="$1"
    local default_value="${2:-}"
    local answer

    if [ -n "${default_value}" ]; then
        read -r -p "${prompt} [${default_value}]: " answer || return 1
        printf '%s' "${answer:-${default_value}}"
        return 0
    fi

    while true; do
        read -r -p "${prompt}: " answer || return 1
        if [ -n "${answer}" ]; then
            printf '%s' "${answer}"
            return 0
        fi
        warn "값을 비워둘 수 없습니다: ${prompt}"
    done
}

promtail_ask_yes_no() {
    local prompt="$1"
    local default_value="${2:-y}"
    local answer

    while true; do
        read -r -p "${prompt} [${default_value}]: " answer || return 1
        answer="${answer:-${default_value}}"
        case "$(printf '%s' "${answer}" | tr '[:upper:]' '[:lower:]')" in
            y|yes)
                return 0
                ;;
            n|no)
                return 1
                ;;
            *)
                warn "y 또는 n으로 입력하세요."
                ;;
        esac
    done
}

promtail_collect_prompt_jobs() {
    local default_host
    local job_name
    local job_label
    local log_path

    can_prompt_secret_values || die "PROMTAIL_MODE=prompt 는 대화형 터미널이 필요합니다. 자동 실행은 PROMTAIL_MODE=auto 또는 RUN_PROMTAIL=0 을 사용하세요."

    default_host="$(promtail_default_host_label)"

    echo "=== Promtail 설정 입력 ==="
    LOKI_PUSH_URL="$(promtail_read_value "Loki push URL" "${LOKI_PUSH_URL}")"
    PROMTAIL_HOST_LABEL="$(promtail_read_value "Grafana/Loki에서 구분할 host 라벨 예: web1" "${PROMTAIL_HOST_LABEL:-${default_host}}")"
    PROMTAIL_ROLE_LABEL="$(promtail_read_value "Grafana/Loki에서 구분할 role 라벨" "${PROMTAIL_ROLE_LABEL:-web}")"

    if promtail_ask_yes_no "공통 시스템 로그 /var/log/*.log, /var/log/syslog 를 수집할까요?" "y"; then
        promtail_add_common_system_logs
    fi

    if promtail_ask_yes_no "Tomcat 로그 ${TOMCAT_HOME}/logs 를 수집할까요?" "y"; then
        promtail_add_job "tomcat" "tomcat-log" "${TOMCAT_HOME}/logs/*.log"
        promtail_add_job "tomcat_out" "tomcat-out" "${TOMCAT_HOME}/logs/catalina.out"
    fi

    while promtail_ask_yes_no "nginx/mysql/bind 같은 추가 로그 경로를 넣을까요?" "n"; do
        job_name="$(promtail_read_value "추가 job_name 예: nginx, mysql, bind")"
        job_label="$(promtail_read_value "Grafana에서 볼 job 라벨" "${job_name}-log")"
        log_path="$(promtail_read_value "수집할 실제 로그 경로 glob 예: /var/log/nginx/*.log")"
        promtail_add_job "${job_name}" "${job_label}" "${log_path}"
    done

    if [ -n "${PROMTAIL_EXTRA_LOGS}" ]; then
        promtail_add_extra_logs "${PROMTAIL_EXTRA_LOGS}"
    fi
}

promtail_check_log_path_glob() {
    local log_path="$1"

    if compgen -G "${log_path}" >/dev/null; then
        log "로그 경로 확인됨: ${log_path}"
    else
        warn "현재 매칭되는 로그 파일이 없습니다: ${log_path}"
        warn "서비스가 아직 로그를 만들지 않았거나 경로가 다를 수 있습니다."
    fi
}

promtail_write_config_to() {
    local output_file="$1"
    local i

    install -d -m 755 "$(dirname "${POSITIONS_FILE}")"

    cat > "${output_file}" <<EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: ${POSITIONS_FILE}

clients:
  - url: "${LOKI_PUSH_URL}"

scrape_configs:
EOF

    for i in "${!PROMTAIL_JOB_NAMES[@]}"; do
        cat >> "${output_file}" <<EOF
  - job_name: "${PROMTAIL_JOB_NAMES[$i]}"
    static_configs:
      - targets:
          - localhost
        labels:
          job: "${PROMTAIL_JOB_LABELS[$i]}"
          host: "${PROMTAIL_HOST_LABEL}"
          role: "${PROMTAIL_ROLE_LABEL}"
          __path__: "${PROMTAIL_LOG_PATHS[$i]}"

EOF
    done
}

promtail_install_binary() {
    local temp_dir

    log "Promtail 패키지 준비: unzip wget"
    apt update
    apt install -y unzip wget

    if command -v promtail >/dev/null 2>&1; then
        log "기존 Promtail 확인:"
        promtail --version || true
    fi

    temp_dir="$(mktemp -d)"

    log "Promtail v${PROMTAIL_VERSION} 다운로드: ${PROMTAIL_DOWNLOAD_URL}"
    if ! (
        cd "${temp_dir}"
        wget -O promtail-linux-amd64.zip "${PROMTAIL_DOWNLOAD_URL}"
        unzip -o promtail-linux-amd64.zip
        install -m 755 promtail-linux-amd64 "${PROMTAIL_BIN}"
    ); then
        rm -rf "${temp_dir}"
        warn "Promtail 다운로드 또는 설치에 실패했습니다."
        return 1
    fi

    rm -rf "${temp_dir}"

    log "Promtail 설치 확인:"
    "${PROMTAIL_BIN}" --version
}

promtail_write_files() {
    local config_tmp="$1"

    log "Promtail 설정 디렉터리 생성"
    install -d -m 755 "$(dirname "${PROMTAIL_CONFIG}")"

    backup_file_or_dir "${PROMTAIL_CONFIG}" >/dev/null || true
    cp "${config_tmp}" "${PROMTAIL_CONFIG}"
    chmod 644 "${PROMTAIL_CONFIG}"
    log "설정 파일 작성: ${PROMTAIL_CONFIG}"

    backup_file_or_dir "${PROMTAIL_SERVICE}" >/dev/null || true
    cat > "${PROMTAIL_SERVICE}" <<EOF
[Unit]
Description=Promtail service
After=network.target

[Service]
Type=simple
User=root
ExecStart=${PROMTAIL_BIN} -config.file=${PROMTAIL_CONFIG}
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    chmod 644 "${PROMTAIL_SERVICE}"
    log "systemd 서비스 작성: ${PROMTAIL_SERVICE}"
}

promtail_install_node_exporter_if_requested() {
    if [ "${INSTALL_NODE_EXPORTER}" != "1" ]; then
        warn "INSTALL_NODE_EXPORTER=0 이므로 node_exporter 설치를 건너뜁니다."
        return 0
    fi

    log "Prometheus node_exporter를 설치/시작합니다."
    apt install -y prometheus-node-exporter
    systemctl enable --now prometheus-node-exporter
    systemctl restart prometheus-node-exporter
}

promtail_check_loki_connection() {
    local ready_url

    if [ "${CHECK_LOKI_READY}" != "1" ]; then
        warn "CHECK_LOKI_READY=0 이므로 Loki /ready 확인을 건너뜁니다."
        return 0
    fi

    ready_url="$(promtail_loki_ready_url)"

    log "Loki 연결 확인: ${ready_url}"
    if wget -qO- --timeout=5 "${ready_url}" >/dev/null 2>&1; then
        log "Loki /ready 응답 확인됨"
    else
        warn "Loki /ready 확인 실패"
        warn "Loki 서버 상태, B-R/C-R ACL, Log 서버 방화벽 3100/tcp를 확인해야 합니다."
    fi
}

promtail_start_service() {
    local service_name

    service_name="$(promtail_service_name)"

    log "Promtail 서비스 반영 및 시작"
    systemctl daemon-reload
    systemctl enable "${service_name}"
    systemctl restart "${service_name}"
    systemctl --no-pager --full status "${service_name}" || true
}

promtail_print_result() {
    local i

    echo "[SUCCESS] Promtail 설정 완료"
    echo "[INFO] mode=${PROMTAIL_MODE}, preset=${PROMTAIL_PRESET}, host=${PROMTAIL_HOST_LABEL}, role=${PROMTAIL_ROLE_LABEL}"
    echo "[INFO] Loki push URL=${LOKI_PUSH_URL}"
    echo "[INFO] 수집 경로:"
    for i in "${!PROMTAIL_JOB_NAMES[@]}"; do
        echo "       ${PROMTAIL_JOB_NAMES[$i]} -> ${PROMTAIL_LOG_PATHS[$i]}"
    done
    echo "[INFO] 확인 명령:"
    echo "       systemctl status $(promtail_service_name) --no-pager"
    echo "       logger \"Hello Loki Test from ${PROMTAIL_HOST_LABEL}\""
    echo "[INFO] Grafana Explore query:"
    echo "       {host=\"${PROMTAIL_HOST_LABEL}\"}"
    echo "       {role=\"${PROMTAIL_ROLE_LABEL}\"}"
}

run_promtail_install_impl() {
    local config_tmp
    local i

    promtail_reset_jobs
    PROMTAIL_HOST_LABEL="${PROMTAIL_HOST_LABEL:-$(promtail_default_host_label)}"
    PROMTAIL_ROLE_LABEL="${PROMTAIL_ROLE_LABEL:-web}"

    case "${PROMTAIL_MODE}" in
        auto)
            log "Promtail auto 설정을 준비합니다."
            promtail_collect_auto_jobs
            ;;
        prompt)
            log "Promtail prompt 설정을 준비합니다."
            promtail_collect_prompt_jobs
            ;;
        *)
            die "지원하지 않는 PROMTAIL_MODE입니다: ${PROMTAIL_MODE}. 사용 가능: auto, prompt, skip"
            ;;
    esac

    promtail_validate_loki_push_url "${LOKI_PUSH_URL}"
    promtail_validate_label_value "host label" "${PROMTAIL_HOST_LABEL}"
    promtail_validate_label_value "role label" "${PROMTAIL_ROLE_LABEL}"

    if [ "${#PROMTAIL_JOB_NAMES[@]}" -eq 0 ]; then
        die "Promtail 수집 경로가 0개입니다. PROMTAIL_MODE=prompt 에서 최소 하나를 선택하거나 PROMTAIL_EXTRA_LOGS를 지정하세요."
    fi

    for i in "${!PROMTAIL_LOG_PATHS[@]}"; do
        promtail_check_log_path_glob "${PROMTAIL_LOG_PATHS[$i]}"
    done

    config_tmp="$(mktemp)"
    promtail_write_config_to "${config_tmp}"

    if [ "${PROMTAIL_MODE}" = "prompt" ]; then
        echo "=== 생성될 Promtail 설정 미리보기 ==="
        sed -n '1,220p' "${config_tmp}"
        if ! promtail_ask_yes_no "이 설정으로 Promtail을 설치/반영할까요?" "y"; then
            rm -f "${config_tmp}"
            warn "Promtail 설정을 취소했습니다."
            return 0
        fi
    fi

    if ! promtail_install_binary ||
        ! promtail_write_files "${config_tmp}" ||
        ! promtail_install_node_exporter_if_requested; then
        rm -f "${config_tmp}"
        return 1
    fi

    rm -f "${config_tmp}"
}

run_promtail_install() {
    if [ "${RUN_PROMTAIL}" != "1" ] || [ "${PROMTAIL_MODE}" = "skip" ]; then
        warn "Promtail 설치를 건너뜁니다."
        return 0
    fi

    if ( run_promtail_install_impl ); then
        log "Promtail 바이너리/설정 설치가 끝났습니다."
        return 0
    fi

    if [ "${PROMTAIL_REQUIRED}" = "1" ]; then
        die "Promtail 설치 실패"
    fi

    warn "Promtail 설치 실패. WEB 서비스 자체는 계속 검증합니다."
}

run_promtail_connect_impl() {
    if ! promtail_check_loki_connection ||
        ! promtail_start_service; then
        return 1
    fi

    promtail_print_result
}

run_promtail_connect() {
    if [ "${RUN_PROMTAIL}" != "1" ] || [ "${PROMTAIL_MODE}" = "skip" ]; then
        return 0
    fi

    if [ ! -x "${PROMTAIL_BIN}" ]; then
        warn "Promtail 바이너리가 없습니다. 설치 단계를 확인하세요."
        return 0
    fi

    if ( run_promtail_connect_impl ); then
        log "Promtail 설정이 끝났습니다."
        return 0
    fi

    if [ "${PROMTAIL_REQUIRED}" = "1" ]; then
        die "Promtail 연결 실패"
    fi

    warn "Promtail 연결 실패. WEB 서비스 자체는 계속 검증합니다."
}

open_firewall_if_requested() {
    if [ "${ALLOW_UFW}" != "1" ]; then
        warn "ALLOW_UFW=0 이므로 UFW 8080/tcp 허용을 건너뜁니다."
        return 0
    fi

    if command -v ufw >/dev/null 2>&1; then
        ufw allow 8080/tcp || true
    else
        warn "ufw 명령을 찾지 못했습니다. 방화벽은 수동 확인하세요."
    fi
}

verify_web() {
    local local_ip
    local app_path="/${APP_CONTEXT}"

    if [ "${APP_CONTEXT}" = "ROOT" ]; then
        app_path=""
    fi

    log "WEB 통합 설치/재구축 결과를 검증합니다."
    systemctl is-active --quiet "${SERVICE_NAME}" || die "${SERVICE_NAME} 이 active 상태가 아닙니다."

    if command -v ss >/dev/null 2>&1; then
        ss -ltn | grep -q ':8080 ' || warn "8080 listen 상태를 ss에서 확인하지 못했습니다."
    fi

    if command -v curl >/dev/null 2>&1; then
        curl -fsS --max-time 5 "http://127.0.0.1:8080${app_path}/" >/dev/null || warn "http://127.0.0.1:8080${app_path}/ 확인 실패. 애플리케이션 상태를 수동 확인하세요."
        curl -fsS --max-time 5 "http://127.0.0.1:8080${app_path}/css/header.css" >/dev/null || warn "http://127.0.0.1:8080${app_path}/css/header.css 확인 실패. static 리소스 배포 상태를 확인하세요."
    fi

    local_ip="$(ip -o -4 addr show | awk '$4 ~ /^192\.168\.2\./ {print $4; exit}' | cut -d/ -f1 || true)"

    echo "[SUCCESS] WEB 통합 설치/재구축 스크립트가 끝났습니다."
    echo "[INFO] 이 서버의 C Zone IP: ${local_ip:-unknown}"
    echo "[INFO] 확인 명령:"
    echo "       systemctl status ${SERVICE_NAME} --no-pager"
    echo "       curl http://127.0.0.1:8080${app_path}/"
    echo "       curl http://127.0.0.1:8080${app_path}/css/header.css"
    echo "       findmnt --mountpoint ${MOUNT_DIR}"
    echo "       ls -l ${ENV_FILE}"
    echo "[INFO] LB 반영 주의:"
    echo "       새 WEB IP가 기존 WEB1/WEB2 IP가 아니면 LB1/LB2의 /etc/nginx/conf.d/load-balancer.conf upstream을 수정해야 합니다."
    echo "       수정 후 LB1/LB2에서 실행: sudo nginx -t && sudo systemctl reload nginx"

    cat > ~/install_smtp587_policy_route.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="setup-smtp587-policy-route.service"
INSTALL_PATH="/usr/local/sbin/setup-smtp587-policy-route.sh"

TABLE_ID="587"
MARK_ID="587"
MARK_HEX="0x24b"
GW="192.168.10.2"
DEV="ens33"
SMTP_HOST="smtp.gmail.com"

apply_rules() {
  echo "===== APPLY SMTP 587 POLICY ROUTE ====="

  ip link show "$DEV" >/dev/null 2>&1 || {
    echo "ERROR: interface $DEV not found"
    exit 1
  }

  ip route replace default via "$GW" dev "$DEV" table "$TABLE_ID"

  if ! ip rule list | grep -Eq "fwmark ${MARK_HEX}.*lookup ${TABLE_ID}"; then
    ip rule add fwmark "$MARK_ID" table "$TABLE_ID" priority 100
  fi

  iptables -t mangle -C OUTPUT -p tcp --dport 587 -j MARK --set-mark "$MARK_ID" 2>/dev/null \
    || iptables -t mangle -A OUTPUT -p tcp --dport 587 -j MARK --set-mark "$MARK_ID"

  echo "OK: TCP/587 -> fwmark $MARK_ID -> table $TABLE_ID -> $GW dev $DEV"
}

install_service() {
  echo "===== INSTALL SELF SCRIPT ====="

  cp "$0" "$INSTALL_PATH"
  chmod 755 "$INSTALL_PATH"
  chown root:root "$INSTALL_PATH"

  echo "===== INSTALL SYSTEMD SERVICE ====="

  cat > "/etc/systemd/system/$SERVICE_NAME" <<SERVICE
[Unit]
Description=Setup SMTP 587 policy route via ens33 NAT
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=$INSTALL_PATH --apply
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE

  systemctl daemon-reload
  systemctl enable --now "$SERVICE_NAME"

  echo "OK: systemd service installed and enabled"
}

verify() {
  echo
  echo "===== VERIFY RULE ====="
  ip rule list | grep -E "fwmark|587" || true

  echo
  echo "===== VERIFY ROUTE TABLE 587 ====="
  ip route show table "$TABLE_ID" || true

  echo
  echo "===== VERIFY IPTABLES MARK ====="
  iptables -t mangle -S OUTPUT | grep 587 || true

  echo
  echo "===== VERIFY SMTP ROUTE ====="
  SMTP4=$(getent ahostsv4 "$SMTP_HOST" | awk 'NR==1{print $1}')
  echo "SMTP4=$SMTP4"

  echo
  echo "[기본 경로]"
  ip -4 route get "$SMTP4" || true

  echo
  echo "[SMTP 587 정책 경로]"
  ip -4 route get "$SMTP4" mark "$MARK_ID" || true

  echo
  echo "[SMTP 587 실제 연결]"
  timeout 5 bash -c "</dev/tcp/$SMTP4/587" && echo "SMTP_587_OK" || echo "SMTP_587_FAIL"
}

remove_all() {
  echo "===== REMOVE SMTP 587 POLICY ROUTE ====="

  iptables -t mangle -D OUTPUT -p tcp --dport 587 -j MARK --set-mark "$MARK_ID" 2>/dev/null || true
  ip rule del fwmark "$MARK_ID" table "$TABLE_ID" priority 100 2>/dev/null || true
  ip route flush table "$TABLE_ID" 2>/dev/null || true

  systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true
  rm -f "/etc/systemd/system/$SERVICE_NAME"
  rm -f "$INSTALL_PATH"
  systemctl daemon-reload

  echo "OK: removed"
}

main() {
  if [ "${EUID}" -ne 0 ]; then
    echo "ERROR: sudo로 실행하세요."
    echo "예: sudo bash ~/install_smtp587_policy_route.sh"
    exit 1
  fi

  case "${1:-install}" in
    install)
      apply_rules
      install_service
      verify
      ;;
    --apply)
      apply_rules
      ;;
    verify)
      verify
      ;;
    remove)
      remove_all
      ;;
    *)
      echo "Usage:"
      echo "  sudo bash $0           # install + apply + verify"
      echo "  sudo bash $0 verify    # verify only"
      echo "  sudo bash $0 remove    # rollback"
      exit 1
      ;;
  esac
}

main "$@"
EOF

chmod 700 ~/install_smtp587_policy_route.sh
echo "       이메일 인증 기능의 포트 개방 스크립트 생성 및 권한부여 완료!"
}

prompt_switch_to_internal_network() {
    echo
    echo "================================================================"
    echo "[INFO] 인터넷 구간 작업이 모두 끝났습니다."
    echo "[INFO] 이제 내부망 통신이 필요한 작업을 시작합니다."
    echo "[INFO]   - NFS mount  : ${NFS_EXPECTED_SOURCE}"
    echo "[INFO]   - Loki 연결  : ${LOKI_PUSH_URL}"
    echo "[INFO] 인터넷 어댑터를 끊고 내부망 어댑터를 연결하세요."
    echo "================================================================"
    read -r -p "준비되면 엔터: "
}

main() {
    require_root

    log "WEB 통합 설치/재구축 시작"
    log "SCRIPT_DIR=${SCRIPT_DIR}"
    log "PROJECT_DIR=${PROJECT_DIR:-auto}"
    log "GIT_URL=${GIT_URL}"
    log "GIT_REMOTE=${GIT_REMOTE}, GIT_BRANCH=${GIT_BRANCH}"
    log "APP_CONTEXT=${APP_CONTEXT}"
    log "BUILT_WAR=${BUILT_WAR:-auto}"
    log "TOMCAT_DOWNLOAD_URL=${TOMCAT_DOWNLOAD_URL}"
    log "TOMCAT_HOME=${TOMCAT_HOME}"
    log "ENV_FILE=${ENV_FILE}"
    log "NFS_VIP=${NFS_VIP}"
    log "RUN_NFS=${RUN_NFS}, RUN_PROMTAIL=${RUN_PROMTAIL}, PROMTAIL_MODE=${PROMTAIL_MODE}, PROMTAIL_PRESET=${PROMTAIL_PRESET}"
    log "ALLOW_DIRTY_REPO=${ALLOW_DIRTY_REPO}, ALLOW_REMOTE_REWRITE=${ALLOW_REMOTE_REWRITE}"

    # === 인터넷 구간 ===
    install_packages
    ensure_build_tools
    ensure_tomcat_user
    install_tomcat_if_needed
    write_tomcat_service
    prepare_source_repo
    normalize_application_properties_location
    validate_repo_layout
    build_war_from_repo
    deploy_built_war_as_ROOT
    wait_for_app_properties
    run_secure_patch
    install_nfs_packages          # NFS 클라이언트 패키지 (apt)
    run_promtail_install          # Promtail 바이너리 + node_exporter (wget/apt)

    # === 네트워크 전환 ===
    prompt_switch_to_internal_network

    # === 내부망 구간 ===
    run_nfs_mount                 # 실제 NFS mount
    run_promtail_connect          # Loki 연결 확인 + 서비스 시작
    open_firewall_if_requested
    verify_web
}

main "$@"
