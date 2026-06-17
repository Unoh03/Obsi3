#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# =====================================================
# WEB 애플리케이션 업데이트 스크립트 (5.9)
#
# 목적:
# - 이미 web-comp_final.sh 로 기본 구축된 WEB 서버에서 애플리케이션 코드만 갱신한다.
# - GitHub repo pull 또는 fresh clone, Maven WAR 빌드, ROOT.war 재배포, DB/Gmail/Redis 설정 재적용, 기본 검증을 수행한다.
#
# 실행 위치:
# - WEB 서버 안에서 실행한다.
# - 신규 서버 최초 구축은 web-comp_final.sh 를 사용한다.
#
# 기본 정책:
# - 기존 repo는 기본적으로 git pull --ff-only 로 갱신한다.
# - FRESH_CLONE=1 이면 기존 /home/*/zzaphub 를 삭제하지 않고 zzaphub.backup.YYYYMMDD-HHMMSS 로 옮긴 뒤 새로 clone한다.
# - Tomcat, NFS, Promtail은 재설치하지 않는다.
# - 새 WAR 배포 뒤 application.properties DB/Gmail/Redis placeholder 패치는 다시 적용한다.
#
# 실행 예시:
#   sudo bash 'web-update_5_9_.sh'
#   sudo PROJECT_DIR=/home/t_web/zzaphub bash 'web-update_5_9_.sh'
#   sudo FRESH_CLONE=1 bash 'web-update_5_9_.sh'
#   sudo REDIS_HOST=192.168.2.7 REDIS_PORT=6379 bash 'web-update_5_9_.sh'
#   sudo RUN_PROMTAIL_CHECK=0 RUN_NFS_CHECK=0 bash 'web-update_5_9_.sh'
# =====================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

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

FRESH_CLONE="${FRESH_CLONE:-0}"
ALLOW_DIRTY_REPO="${ALLOW_DIRTY_REPO:-0}"
ALLOW_REMOTE_REWRITE="${ALLOW_REMOTE_REWRITE:-0}"
ALLOW_NONSTANDARD_FRESH_CLONE="${ALLOW_NONSTANDARD_FRESH_CLONE:-0}"
INSTALL_BUILD_TOOLS="${INSTALL_BUILD_TOOLS:-1}"

ENV_FILE="${ENV_FILE:-/etc/zzaphub-db.env}"
PROP_FILE="${PROP_FILE:-${TOMCAT_HOME}/webapps/${APP_CONTEXT}/WEB-INF/classes/application.properties}"
WAR_FILE="${WAR_FILE:-${TOMCAT_HOME}/webapps/${APP_CONTEXT}.war}"
DROPIN_DIR="${DROPIN_DIR:-/etc/systemd/system/${SERVICE_NAME}.d}"
DROPIN_FILE="${DROPIN_FILE:-${DROPIN_DIR}/10-zzaphub-db-env.conf}"

NFS_VIP="${NFS_VIP:-192.168.2.50}"
NFS_REMOTE_SHARE="${NFS_REMOTE_SHARE:-/share_directory}"
MOUNT_DIR="${MOUNT_DIR:-${TOMCAT_HOME}/webapps/upload}"
NFS_EXPECTED_SOURCE="${NFS_VIP}:${NFS_REMOTE_SHARE}"
RUN_NFS_CHECK="${RUN_NFS_CHECK:-1}"
NFS_CHECK_REQUIRED="${NFS_CHECK_REQUIRED:-1}"
REDIS_HOST="${REDIS_HOST:-192.168.2.7}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_REQUIRED="${REDIS_REQUIRED:-1}"
CHECK_REDIS_READY="${CHECK_REDIS_READY:-1}"

RUN_SECURE="${RUN_SECURE:-1}"
UPDATE_WAR="${UPDATE_WAR:-1}"
RUN_PROMTAIL_CHECK="${RUN_PROMTAIL_CHECK:-1}"
PROMTAIL_CHECK_REQUIRED="${PROMTAIL_CHECK_REQUIRED:-0}"
PROMTAIL_SERVICE="${PROMTAIL_SERVICE:-/etc/systemd/system/promtail.service}"
RUN_LOKI_READY_CHECK="${RUN_LOKI_READY_CHECK:-0}"
PROMPT_INTERNAL_NETWORK="${PROMPT_INTERNAL_NETWORK:-1}"
LOKI_PUSH_URL="${LOKI_PUSH_URL:-http://1.2.3.3:3100/loki/api/v1/push}"

WEB_VERIFY_WAIT="${WEB_VERIFY_WAIT:-30}"
WEB_HTTP_REQUIRED="${WEB_HTTP_REQUIRED:-0}"

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/zzaphub-web-update}"
RUN_ID="$(date +%Y%m%d-%H%M%S)"

EXPECTED_MASTER_DB_URL='${MASTER_DB_URL}'
EXPECTED_MASTER_DB_USER='${MASTER_DB_USER}'
EXPECTED_MASTER_DB_PASSWORD='${MASTER_DB_PASSWORD}'
EXPECTED_SLAVE_DB_URL='${SLAVE_DB_URL}'
EXPECTED_SLAVE_DB_USER='${SLAVE_DB_USER}'
EXPECTED_SLAVE_DB_PASSWORD='${SLAVE_DB_PASSWORD}'
EXPECTED_MAIL_USERNAME='${MAIL_USERNAME}'
EXPECTED_MAIL_PASSWORD='${MAIL_PASSWORD}'
EXPECTED_REDIS_HOST='${REDIS_HOST}'
EXPECTED_REDIS_PORT='${REDIS_PORT}'

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
    cp -a "${path}" "${backup_path}"
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
        '${MASTER_DB_URL}'|'${MASTER_DB_USER}'|'${MASTER_DB_PASSWORD}'|'${SLAVE_DB_URL}'|'${SLAVE_DB_USER}'|'${SLAVE_DB_PASSWORD}'|'${MAIL_USERNAME}'|'${MAIL_PASSWORD}'|'${REDIS_HOST}'|'${REDIS_PORT}'|'${REDIS_HOST:192.168.2.7}'|'${REDIS_PORT:6379}')
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

env_file_has_all_redis_vars() {
    env_file_var_ready "REDIS_HOST" &&
    env_file_var_ready "REDIS_PORT"
}

env_file_has_all_secure_vars() {
    env_file_has_all_db_vars && env_file_has_all_mail_vars && env_file_has_all_redis_vars
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
    warn "방법 1: 터미널에서 sudo bash 'web-update_5_9_.sh' 로 실행해 질문에 답하세요."
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
REDIS_HOST='192.168.2.7'
REDIS_PORT='6379'
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
    local redis_host="${REDIS_HOST:-192.168.2.7}"
    local redis_port="${REDIS_PORT:-6379}"
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
        redis_host="${redis_host:-$(get_property "spring.data.redis.host" "${PROP_FILE}")}"
        redis_port="${redis_port:-$(get_property "spring.data.redis.port" "${PROP_FILE}")}"
    fi

    mail_password="${mail_password// /}"
    redis_host="${redis_host:-192.168.2.7}"
    redis_port="${redis_port:-6379}"

    prompt_env_var_if_needed "MASTER_DB_URL" "MASTER_DB_URL" "0" "master_db_url" || missing_keys+=("MASTER_DB_URL")
    prompt_env_var_if_needed "MASTER_DB_USER" "MASTER_DB_USER" "0" "master_db_user" || missing_keys+=("MASTER_DB_USER")
    prompt_env_var_if_needed "MASTER_DB_PASSWORD" "MASTER_DB_PASSWORD" "1" "master_db_password" || missing_keys+=("MASTER_DB_PASSWORD")
    prompt_env_var_if_needed "SLAVE_DB_URL" "SLAVE_DB_URL" "0" "slave_db_url" || missing_keys+=("SLAVE_DB_URL")
    prompt_env_var_if_needed "SLAVE_DB_USER" "SLAVE_DB_USER" "0" "slave_db_user" || missing_keys+=("SLAVE_DB_USER")
    prompt_env_var_if_needed "SLAVE_DB_PASSWORD" "SLAVE_DB_PASSWORD" "1" "slave_db_password" || missing_keys+=("SLAVE_DB_PASSWORD")
    prompt_env_var_if_needed "MAIL_USERNAME" "MAIL_USERNAME" "0" "mail_username" || missing_keys+=("MAIL_USERNAME")
    prompt_env_var_if_needed "MAIL_PASSWORD" "MAIL_PASSWORD" "1" "mail_password" || missing_keys+=("MAIL_PASSWORD")
    prompt_env_var_if_needed "REDIS_HOST" "REDIS_HOST" "0" "redis_host" || missing_keys+=("REDIS_HOST")
    prompt_env_var_if_needed "REDIS_PORT" "REDIS_PORT" "0" "redis_port" || missing_keys+=("REDIS_PORT")
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
# zzaphub DB, mail, and Redis runtime settings
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
    append_env_var_if_missing "REDIS_HOST" "${redis_host}" || missing=1
    append_env_var_if_missing "REDIS_PORT" "${redis_port}" || missing=1

    chmod 600 "${ENV_FILE}"
    chown root:root "${ENV_FILE}" 2>/dev/null || true

    if [ "${missing}" -ne 0 ]; then
        die "${ENV_FILE} 에 MASTER_DB_*/SLAVE_DB_* 6개, MAIL_USERNAME/MAIL_PASSWORD, REDIS_HOST/REDIS_PORT 값을 채울 수 없습니다. 환경변수로 넘기거나 파일을 직접 작성하세요."
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

redis_session_properties_configured() {
    [ "$(get_property "spring.session.store-type" "${PROP_FILE}")" = "redis" ] &&
    [ "$(get_property "spring.session.redis.namespace" "${PROP_FILE}")" = "zzaphub:session" ] &&
    [ "$(get_property "spring.data.redis.host" "${PROP_FILE}")" = "${EXPECTED_REDIS_HOST}" ] &&
    [ "$(get_property "spring.data.redis.port" "${PROP_FILE}")" = "${EXPECTED_REDIS_PORT}" ] &&
    [ "$(get_property "spring.data.redis.timeout" "${PROP_FILE}")" = "3s" ] &&
    [ "$(get_property "server.servlet.session.timeout" "${PROP_FILE}")" = "30m" ] &&
    [ "$(get_property "server.servlet.session.cookie.http-only" "${PROP_FILE}")" = "true" ] &&
    [ "$(get_property "server.servlet.session.cookie.same-site" "${PROP_FILE}")" = "lax" ]
}

ensure_redis_session_properties() {
    set_property "spring.session.store-type" "redis" "${PROP_FILE}"
    set_property "spring.session.redis.namespace" "zzaphub:session" "${PROP_FILE}"
    set_property "spring.data.redis.host" "${EXPECTED_REDIS_HOST}" "${PROP_FILE}"
    set_property "spring.data.redis.port" "${EXPECTED_REDIS_PORT}" "${PROP_FILE}"
    set_property "spring.data.redis.timeout" "3s" "${PROP_FILE}"
    set_property "server.servlet.session.timeout" "30m" "${PROP_FILE}"
    set_property "server.servlet.session.cookie.http-only" "true" "${PROP_FILE}"
    set_property "server.servlet.session.cookie.same-site" "lax" "${PROP_FILE}"
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
    local redis_session_ready=0

    if properties_already_secure; then
        properties_secure=1
    fi

    if mail_transport_already_configured; then
        mail_transport_ready=1
    fi

    if redis_session_properties_configured; then
        redis_session_ready=1
    fi

    if [ "${properties_secure}" -eq 1 ] && [ "${mail_transport_ready}" -eq 1 ] && [ "${redis_session_ready}" -eq 1 ]; then
        log "application.properties 는 이미 DB/Gmail/Redis 환경변수 placeholder 와 Gmail SMTP/Redis 세션 설정을 사용합니다."
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

    if [ "${redis_session_ready}" -ne 1 ]; then
        ensure_redis_session_properties
        log "application.properties 의 Redis 세션 설정을 보정했습니다."
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
    [ "$(get_property "spring.session.store-type" "${PROP_FILE}")" = "redis" ] || failed=1
    [ "$(get_property "spring.session.redis.namespace" "${PROP_FILE}")" = "zzaphub:session" ] || failed=1
    [ "$(get_property "spring.data.redis.host" "${PROP_FILE}")" = "${EXPECTED_REDIS_HOST}" ] || failed=1
    [ "$(get_property "spring.data.redis.port" "${PROP_FILE}")" = "${EXPECTED_REDIS_PORT}" ] || failed=1
    [ "$(get_property "spring.data.redis.timeout" "${PROP_FILE}")" = "3s" ] || failed=1
    [ "$(get_property "server.servlet.session.timeout" "${PROP_FILE}")" = "30m" ] || failed=1
    [ "$(get_property "server.servlet.session.cookie.http-only" "${PROP_FILE}")" = "true" ] || failed=1
    [ "$(get_property "server.servlet.session.cookie.same-site" "${PROP_FILE}")" = "lax" ] || failed=1
    env_file_has_all_secure_vars || failed=1
    [ -f "${DROPIN_FILE}" ] && grep -Fq "EnvironmentFile=${ENV_FILE}" "${DROPIN_FILE}" || failed=1

    if [ "${failed}" -ne 0 ]; then
        die "DB/Gmail/Redis 설정 재적용 검증 실패"
    fi

    log "DB/Gmail secret 재적용 및 Redis 세션 설정 검증 완료"
}

ensure_existing_web_base() {
    command -v systemctl >/dev/null 2>&1 || die "systemctl 명령을 찾지 못했습니다."
    [ -x "${TOMCAT_HOME}/bin/startup.sh" ] || die "Tomcat 설치를 찾지 못했습니다: ${TOMCAT_HOME}"
    systemctl cat "${SERVICE_NAME}" >/dev/null 2>&1 || die "Tomcat systemd 서비스를 찾지 못했습니다: ${SERVICE_NAME}"
}

ensure_build_tools() {
    local packages=()

    command -v git >/dev/null 2>&1 || packages+=("git")
    command -v mvn >/dev/null 2>&1 || packages+=("maven")
    command -v java >/dev/null 2>&1 || packages+=("openjdk-17-jdk")
    command -v jar >/dev/null 2>&1 || packages+=("openjdk-17-jdk")
    command -v redis-cli >/dev/null 2>&1 || packages+=("redis-tools")

    if [ "${#packages[@]}" -eq 0 ]; then
        log "Git/Maven/JDK/redis-tools 도구가 이미 준비되어 있습니다."
        return 0
    fi

    if [ "${INSTALL_BUILD_TOOLS}" != "1" ]; then
        die "필수 빌드 도구가 없습니다: ${packages[*]}. 설치하려면 INSTALL_BUILD_TOOLS=1 로 실행하세요."
    fi

    log "부족한 빌드 도구를 설치합니다: ${packages[*]}"
    apt update
    apt install -y "${packages[@]}"
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

backup_existing_project_dir_for_fresh_clone() {
    local backup_dir="${PROJECT_DIR}.backup.${RUN_ID}"

    [ -e "${PROJECT_DIR}" ] || return 0

    if [ "${ALLOW_NONSTANDARD_FRESH_CLONE}" != "1" ]; then
        case "${PROJECT_DIR}" in
            /home/*/zzaphub)
                ;;
            *)
                die "FRESH_CLONE=1 은 기본적으로 /home/*/zzaphub 만 백업 이동합니다. 현재: ${PROJECT_DIR}. 계속하려면 ALLOW_NONSTANDARD_FRESH_CLONE=1 을 지정하세요."
                ;;
        esac
    fi

    if mountpoint -q "${PROJECT_DIR}" 2>/dev/null; then
        die "PROJECT_DIR 자체가 mountpoint 입니다. 자동 이동하지 않습니다: ${PROJECT_DIR}"
    fi

    [ ! -e "${backup_dir}" ] || die "백업 경로가 이미 있습니다: ${backup_dir}"
    log "기존 repo를 삭제하지 않고 백업 이동합니다: ${PROJECT_DIR} -> ${backup_dir}"
    mv -- "${PROJECT_DIR}" "${backup_dir}"
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

prepare_source_repo_for_update() {
    resolve_project_dir
    log "소스 repo 경로: ${PROJECT_DIR}"

    if [ "${FRESH_CLONE}" = "1" ]; then
        backup_existing_project_dir_for_fresh_clone
        clone_source_repo
        return 0
    fi

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
        warn "RUN_SECURE=0 이므로 DB/Gmail secret 재적용과 Redis 세션 설정 보정을 건너뜁니다."
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
}

verify_nfs_mount() {
    local mount_count
    local current_source

    if [ "${RUN_NFS_CHECK}" != "1" ]; then
        warn "RUN_NFS_CHECK=0 이므로 NFS upload mount 확인을 건너뜁니다."
        return 0
    fi

    if ! command -v findmnt >/dev/null 2>&1; then
        warn "findmnt 명령을 찾지 못해 NFS mount 확인을 건너뜁니다."
        return 0
    fi

    if ! nfs_is_mounted; then
        if [ "${NFS_CHECK_REQUIRED}" = "1" ]; then
            die "${MOUNT_DIR} 가 mount되어 있지 않습니다. web-comp_final.sh 또는 수동 mount 상태를 확인하세요."
        fi
        warn "${MOUNT_DIR} 가 mount되어 있지 않습니다."
        return 0
    fi

    mount_count="$(nfs_mount_source_count)"
    if [ "${mount_count}" -gt 1 ]; then
        print_nfs_mount_status
        die "${MOUNT_DIR} 에 중복 mount가 있습니다. 수동 umount 후 확인하세요."
    fi

    current_source="$(nfs_current_mount_source)"
    if ! nfs_is_expected_source "${current_source}"; then
        print_nfs_mount_status
        die "${MOUNT_DIR} mount source가 기대값과 다릅니다. 현재: ${current_source:-unknown}, 기대: ${NFS_EXPECTED_SOURCE}"
    fi

    log "NFS upload mount 확인 완료: ${current_source} -> ${MOUNT_DIR}"
    print_nfs_mount_status
}

verify_redis_connection() {
    local redis_host="${REDIS_HOST}"
    local redis_port="${REDIS_PORT}"

    if [ "${CHECK_REDIS_READY}" != "1" ]; then
        warn "CHECK_REDIS_READY=0 이므로 Redis 연결 확인을 건너뜁니다."
        return 0
    fi

    if env_file_var_ready "REDIS_HOST"; then
        redis_host="$(get_env_file_value "REDIS_HOST")"
    fi
    if env_file_var_ready "REDIS_PORT"; then
        redis_port="$(get_env_file_value "REDIS_PORT")"
    fi

    if ! command -v redis-cli >/dev/null 2>&1; then
        if [ "${REDIS_REQUIRED}" = "1" ]; then
            die "redis-cli 명령을 찾지 못했습니다. redis-tools 설치 상태를 확인하세요."
        fi
        warn "redis-cli 명령을 찾지 못해 Redis 연결 확인을 건너뜁니다."
        return 0
    fi

    log "Redis 연결 확인: ${redis_host}:${redis_port}"
    if timeout 5s redis-cli -h "${redis_host}" -p "${redis_port}" ping | grep -q '^PONG$'; then
        log "Redis PONG 응답 확인됨"
        return 0
    fi

    if [ "${REDIS_REQUIRED}" = "1" ]; then
        die "Redis 연결 확인 실패: ${redis_host}:${redis_port}. Cache 서버, redis-server bind/protected-mode, 방화벽/ACL 6379/tcp를 확인하세요."
    fi

    warn "Redis 연결 확인 실패: ${redis_host}:${redis_port}. 로그인 세션 공유가 동작하지 않을 수 있습니다."
}

promtail_service_name() {
    local service_name

    service_name="$(basename "${PROMTAIL_SERVICE}")"
    printf '%s' "${service_name%.service}"
}

promtail_loki_ready_url() {
    printf '%s' "${LOKI_PUSH_URL%/loki/api/v1/push}/ready"
}

verify_promtail_service() {
    local service_name

    if [ "${RUN_PROMTAIL_CHECK}" != "1" ]; then
        warn "RUN_PROMTAIL_CHECK=0 이므로 Promtail 확인을 건너뜁니다."
        return 0
    fi

    service_name="$(promtail_service_name)"
    if systemctl is-active --quiet "${service_name}"; then
        log "Promtail 서비스 active 확인: ${service_name}"
        return 0
    fi

    if [ "${PROMTAIL_CHECK_REQUIRED}" = "1" ]; then
        die "Promtail 서비스가 active 상태가 아닙니다: ${service_name}"
    fi

    warn "Promtail 서비스가 active 상태가 아닙니다: ${service_name}"
}

prompt_switch_to_internal_network_if_needed() {
    if [ "${PROMPT_INTERNAL_NETWORK}" != "1" ]; then
        return 0
    fi

    if [ "${RUN_NFS_CHECK}" != "1" ] && [ "${CHECK_REDIS_READY}" != "1" ] && [ "${RUN_LOKI_READY_CHECK}" != "1" ]; then
        return 0
    fi

    echo
    echo "================================================================"
    echo "[INFO] GitHub pull/build/deploy 구간이 끝났습니다."
    echo "[INFO] NFS/Redis/Loki 확인은 내부망 통신이 필요합니다."
    echo "[INFO] 필요하면 인터넷 어댑터를 끊고 내부망 어댑터를 연결하세요."
    if [ "${RUN_NFS_CHECK}" = "1" ]; then
        echo "[INFO]   - NFS mount : ${NFS_EXPECTED_SOURCE}"
    fi
    if [ "${CHECK_REDIS_READY}" = "1" ]; then
        echo "[INFO]   - Redis 연결: ${REDIS_HOST}:${REDIS_PORT}"
    fi
    if [ "${RUN_LOKI_READY_CHECK}" = "1" ]; then
        echo "[INFO]   - Loki 연결: ${LOKI_PUSH_URL}"
    fi
    echo "================================================================"
    read -r -p "준비되면 엔터: "
}

check_loki_ready_if_requested() {
    local ready_url

    if [ "${RUN_LOKI_READY_CHECK}" != "1" ]; then
        return 0
    fi

    ready_url="$(promtail_loki_ready_url)"
    log "Loki 연결 확인: ${ready_url}"
    if wget -qO- --timeout=5 "${ready_url}" >/dev/null 2>&1; then
        log "Loki /ready 응답 확인됨"
    else
        warn "Loki /ready 확인 실패. Log 서버 상태, ACL, 방화벽 3100/tcp를 확인하세요."
    fi
}

verify_web() {
    local local_ip
    local app_path="/${APP_CONTEXT}"
    local waited=0
    local root_url
    local css_url
    local root_ok=0

    if [ "${APP_CONTEXT}" = "ROOT" ]; then
        app_path=""
    fi

    root_url="http://127.0.0.1:8080${app_path}/"
    css_url="http://127.0.0.1:8080${app_path}/css/header.css"

    log "WEB 업데이트 결과를 검증합니다."
    systemctl is-active --quiet "${SERVICE_NAME}" || die "${SERVICE_NAME} 이 active 상태가 아닙니다."

    if command -v ss >/dev/null 2>&1; then
        ss -ltn | grep -q ':8080 ' || warn "8080 listen 상태를 ss에서 확인하지 못했습니다."
    fi

    if command -v curl >/dev/null 2>&1; then
        while [ "${waited}" -lt "${WEB_VERIFY_WAIT}" ]; do
            if curl -fsS --max-time 5 "${root_url}" >/dev/null; then
                root_ok=1
                break
            fi
            sleep 2
            waited=$((waited + 2))
            echo "[INFO] WEB 응답 대기 중... (${waited}/${WEB_VERIFY_WAIT}s)"
        done

        if [ "${root_ok}" -ne 1 ]; then
            if [ "${WEB_HTTP_REQUIRED}" = "1" ]; then
                die "${root_url} 확인 실패"
            fi
            warn "${root_url} 확인 실패. 애플리케이션 상태를 수동 확인하세요."
        fi

        curl -fsS --max-time 5 "${css_url}" >/dev/null || warn "${css_url} 확인 실패. static 리소스 배포 상태를 확인하세요."
    fi

    local_ip="$(ip -o -4 addr show 2>/dev/null | awk '$4 ~ /^192\.168\.2\./ {print $4; exit}' | cut -d/ -f1 || true)"

    echo "[SUCCESS] WEB 애플리케이션 업데이트가 끝났습니다."
    echo "[INFO] 이 서버의 C Zone IP: ${local_ip:-unknown}"
    echo "[INFO] 확인 명령:"
    echo "       systemctl status ${SERVICE_NAME} --no-pager"
    echo "       curl ${root_url}"
    echo "       curl ${css_url}"
    echo "       findmnt --mountpoint ${MOUNT_DIR}"
    echo "       ls -l ${ENV_FILE}"
    echo "[INFO] LB 반영 주의:"
    echo "       새 WEB IP가 기존 WEB1/WEB2 IP가 아니면 LB1/LB2의 /etc/nginx/conf.d/load-balancer.conf upstream을 수정해야 합니다."
    echo "       수정 후 LB1/LB2에서 실행: sudo nginx -t && sudo systemctl reload nginx"
}

main() {
    require_root

    log "WEB 애플리케이션 업데이트 시작"
    log "SCRIPT_DIR=${SCRIPT_DIR}"
    log "PROJECT_DIR=${PROJECT_DIR:-auto}"
    log "GIT_URL=${GIT_URL}"
    log "GIT_REMOTE=${GIT_REMOTE}, GIT_BRANCH=${GIT_BRANCH}"
    log "FRESH_CLONE=${FRESH_CLONE}"
    log "APP_CONTEXT=${APP_CONTEXT}, TOMCAT_HOME=${TOMCAT_HOME}"
    log "REDIS_HOST=${REDIS_HOST}, REDIS_PORT=${REDIS_PORT}, CHECK_REDIS_READY=${CHECK_REDIS_READY}"
    log "RUN_SECURE=${RUN_SECURE}, RUN_NFS_CHECK=${RUN_NFS_CHECK}, RUN_PROMTAIL_CHECK=${RUN_PROMTAIL_CHECK}, RUN_LOKI_READY_CHECK=${RUN_LOKI_READY_CHECK}"

    ensure_existing_web_base
    ensure_build_tools
    prepare_source_repo_for_update
    normalize_application_properties_location
    validate_repo_layout
    build_war_from_repo
    deploy_built_war_as_ROOT
    wait_for_app_properties
    run_secure_patch
    prompt_switch_to_internal_network_if_needed
    verify_nfs_mount
    verify_redis_connection
    verify_promtail_service
    check_loki_ready_if_requested
    verify_web
}

main "$@"
