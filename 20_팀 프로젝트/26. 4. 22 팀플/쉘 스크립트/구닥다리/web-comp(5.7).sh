#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# =====================================================
# WEB 통합 설치/재구축 스크립트 (5.6)
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
# - WEB 서버의 /home/*/zzaphub 또는 PROJECT_DIR 경로에 GitHub repo clone이 있어야 한다.
# - repo는 src/main/resources/application.properties, mappers, static 구조여야 한다.
# - 같은 디렉터리에 promtail-client-auto(5.6).sh 가 있으면 WEB 로그 수집 설정을 맡긴다.
#
# 내장 기능:
# - Tomcat 설치
# - repo pull/build 후 ROOT.war 배포
# - DB/Gmail secret 분리
# - NFS VIP upload mount
#
# 실행 예시:
#   sudo bash 'web-comp.sh'
#   sudo PROJECT_DIR=/home/t_web/zzaphub RUN_PROMTAIL=0 bash 'web-comp.sh'
#
# 자동화/비대화형 실행 예시:
#   sudo MASTER_DB_URL='jdbc:mariadb://1.2.3.1:3306/care' MASTER_DB_USER='web' MASTER_DB_PASSWORD='값은직접입력' \
#        SLAVE_DB_URL='jdbc:mariadb://1.2.3.2:3306/care' SLAVE_DB_USER='web' SLAVE_DB_PASSWORD='값은직접입력' \
#        MAIL_USERNAME='발신용Gmail주소' MAIL_PASSWORD='Gmail앱비밀번호' \
#        bash 'web-comp.sh'
#
# 이미 /etc/zzaphub-db.env 가 준비되어 있다면:
#   sudo bash 'web-comp.sh'
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
GIT_REMOTE="${GIT_REMOTE:-origin}"
GIT_BRANCH="${GIT_BRANCH:-main}"
BUILT_WAR="${BUILT_WAR:-}"
PROMTAIL_SCRIPT="${PROMTAIL_SCRIPT:-${SCRIPT_DIR}/promtail-client-auto(5.6).sh}"

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
PROMTAIL_PRESET="${PROMTAIL_PRESET:-web}"
PROMTAIL_HOST_LABEL="${PROMTAIL_HOST_LABEL:-}"
ALLOW_UFW="${ALLOW_UFW:-1}"

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

env_file_has_all_db_vars() {
    [ -f "${ENV_FILE}" ] &&
    grep -Eq '^[[:space:]]*MASTER_DB_URL=' "${ENV_FILE}" &&
    grep -Eq '^[[:space:]]*MASTER_DB_USER=' "${ENV_FILE}" &&
    grep -Eq '^[[:space:]]*MASTER_DB_PASSWORD=' "${ENV_FILE}" &&
    grep -Eq '^[[:space:]]*SLAVE_DB_URL=' "${ENV_FILE}" &&
    grep -Eq '^[[:space:]]*SLAVE_DB_USER=' "${ENV_FILE}" &&
    grep -Eq '^[[:space:]]*SLAVE_DB_PASSWORD=' "${ENV_FILE}"
}

env_file_has_all_mail_vars() {
    [ -f "${ENV_FILE}" ] &&
    grep -Eq '^[[:space:]]*MAIL_USERNAME=' "${ENV_FILE}" &&
    grep -Eq '^[[:space:]]*MAIL_PASSWORD=' "${ENV_FILE}"
}

env_file_has_all_secure_vars() {
    env_file_has_all_db_vars && env_file_has_all_mail_vars
}

append_env_var_if_missing() {
    local env_key="$1"
    local env_value="$2"

    if env_has_var "${env_key}"; then
        log "${ENV_FILE} 에 ${env_key} 가 이미 있습니다. 값은 출력하지 않습니다."
        return 0
    fi

    if [ -z "${env_value}" ] || is_placeholder "${env_value}"; then
        return 1
    fi

    printf '%s=%s\n' "${env_key}" "$(quote_env_value "${env_value}")" >> "${ENV_FILE}"
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

    if env_has_var "${env_key}"; then
        return 0
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
    warn "방법 1: 터미널에서 sudo bash 'web-comp.sh' 로 실행해 질문에 답하세요."
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

secure_application_properties() {
    if properties_already_secure; then
        log "application.properties 는 이미 환경변수 placeholder 를 사용합니다."
        return 0
    fi

    log "application.properties 백업: $(backup_file_or_dir "${PROP_FILE}")"

    set_property "spring.datasource.master.jdbc-url" "${EXPECTED_MASTER_DB_URL}" "${PROP_FILE}"
    set_property "spring.datasource.master.username" "${EXPECTED_MASTER_DB_USER}" "${PROP_FILE}"
    set_property "spring.datasource.master.password" "${EXPECTED_MASTER_DB_PASSWORD}" "${PROP_FILE}"
    set_property "spring.datasource.slave.jdbc-url" "${EXPECTED_SLAVE_DB_URL}" "${PROP_FILE}"
    set_property "spring.datasource.slave.username" "${EXPECTED_SLAVE_DB_USER}" "${PROP_FILE}"
    set_property "spring.datasource.slave.password" "${EXPECTED_SLAVE_DB_PASSWORD}" "${PROP_FILE}"
    set_property "spring.mail.username" "${EXPECTED_MAIL_USERNAME}" "${PROP_FILE}"
    set_property "spring.mail.password" "${EXPECTED_MAIL_PASSWORD}" "${PROP_FILE}"

    log "application.properties 의 master/slave DB 접속정보와 Gmail 발신 계정을 환경변수 placeholder 로 변경했습니다."
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

    if [ -n "${PROJECT_DIR}" ]; then
        [ -d "${PROJECT_DIR}" ] || die "PROJECT_DIR 경로가 없습니다: ${PROJECT_DIR}"
        [ -d "${PROJECT_DIR}/.git" ] || die "PROJECT_DIR 이 Git repo가 아닙니다: ${PROJECT_DIR}"
        return 0
    fi

    for candidate in /home/*/zzaphub; do
        [ -d "${candidate}/.git" ] || continue
        candidates+=("${candidate}")
    done

    case "${#candidates[@]}" in
        0)
            die "/home/*/zzaphub Git repo를 찾지 못했습니다. PROJECT_DIR=/home/사용자/zzaphub 를 지정하세요."
            ;;
        1)
            PROJECT_DIR="${candidates[0]}"
            ;;
        *)
            warn "zzaphub repo 후보가 여러 개입니다:"
            printf '  %s\n' "${candidates[@]}" >&2
            die "PROJECT_DIR=/home/사용자/zzaphub 를 지정하세요."
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

prepare_source_repo() {
    resolve_project_dir
    log "소스 repo 경로: ${PROJECT_DIR}"
    log "Git 최신 코드 반영: ${GIT_REMOTE} ${GIT_BRANCH}"
    run_in_project_dir git pull "${GIT_REMOTE}" "${GIT_BRANCH}"
}

validate_repo_layout() {
    local resource_dir="${PROJECT_DIR}/src/main/resources"

    [ -f "${resource_dir}/application.properties" ] ||
        die "${resource_dir}/application.properties 가 없습니다. application.properties는 src/main/resources 아래에 있어야 합니다."

    [ -d "${resource_dir}/mappers" ] ||
        die "${resource_dir}/mappers 디렉터리가 없습니다. MyBatis mapper XML은 src/main/resources/mappers 아래에 있어야 합니다."

    [ -d "${resource_dir}/static" ] ||
        die "${resource_dir}/static 디렉터리가 없습니다. CSS 정적 리소스 누락 재발을 막기 위해 중단합니다."

    if [ -f "${PROJECT_DIR}/src/main/java/application.properties" ]; then
        warn "${PROJECT_DIR}/src/main/java/application.properties 가 아직 남아 있습니다. repo 정리 대상입니다."
    fi
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

run_nfs_mount() {
    local mount_count
    local current_source

    if [ "${RUN_NFS}" != "1" ]; then
        warn "RUN_NFS=0 이므로 NFS upload mount를 건너뜁니다."
        return 0
    fi

    log "내장 NFS VIP upload mount를 시작합니다."
    log "NFS source=${NFS_EXPECTED_SOURCE}, mount=${MOUNT_DIR}"

    apt install -y nfs-common lsof
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

run_promtail_client() {
    if [ "${RUN_PROMTAIL}" != "1" ]; then
        warn "RUN_PROMTAIL=0 이므로 Promtail 로그 수집 설정을 건너뜁니다."
        return 0
    fi

    if [ ! -f "${PROMTAIL_SCRIPT}" ]; then
        if [ "${PROMTAIL_REQUIRED}" = "1" ]; then
            die "Promtail 자동 설정 스크립트를 찾을 수 없습니다: ${PROMTAIL_SCRIPT}"
        fi

        warn "Promtail 자동 설정 스크립트를 찾을 수 없어 건너뜁니다: ${PROMTAIL_SCRIPT}"
        return 0
    fi

    log "Promtail WEB preset 설정을 실행합니다."

    if PROMTAIL_PRESET="${PROMTAIL_PRESET}" \
        HOST_LABEL="${PROMTAIL_HOST_LABEL}" \
        ROLE_LABEL="web" \
        TOMCAT_HOME="${TOMCAT_HOME}" \
        LOKI_PUSH_URL="${LOKI_PUSH_URL:-http://1.2.3.3:3100/loki/api/v1/push}" \
        bash "${PROMTAIL_SCRIPT}"; then
        log "Promtail WEB preset 설정이 끝났습니다."
        return 0
    fi

    if [ "${PROMTAIL_REQUIRED}" = "1" ]; then
        die "Promtail WEB preset 설정 실패"
    fi

    warn "Promtail WEB preset 설정 실패. WEB 서비스 자체는 계속 검증합니다."
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
}

main() {
    require_root

    log "WEB 통합 설치/재구축 시작"
    log "SCRIPT_DIR=${SCRIPT_DIR}"
    log "PROJECT_DIR=${PROJECT_DIR:-auto}"
    log "GIT_REMOTE=${GIT_REMOTE}, GIT_BRANCH=${GIT_BRANCH}"
    log "APP_CONTEXT=${APP_CONTEXT}"
    log "BUILT_WAR=${BUILT_WAR:-auto}"
    log "TOMCAT_DOWNLOAD_URL=${TOMCAT_DOWNLOAD_URL}"
    log "TOMCAT_HOME=${TOMCAT_HOME}"
    log "ENV_FILE=${ENV_FILE}"
    log "NFS_VIP=${NFS_VIP}"
    log "RUN_NFS=${RUN_NFS}, RUN_PROMTAIL=${RUN_PROMTAIL}, PROMTAIL_PRESET=${PROMTAIL_PRESET}"

    install_packages
    ensure_build_tools
    ensure_tomcat_user
    install_tomcat_if_needed
    write_tomcat_service
    prepare_source_repo
    validate_repo_layout
    build_war_from_repo
    deploy_built_war_as_ROOT
    wait_for_app_properties
    run_secure_patch
    run_nfs_mount
    run_promtail_client
    open_firewall_if_requested
    verify_web
}

main "$@"
