#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# WEB 보안 패치 스크립트
#
# 목적:
# - 이미 배포되어 실행 중인 zzaphub Tomcat WEB 서버에서 DB/Gmail secret만 분리한다.
# - WEB 재구축, git pull, Maven build, WAR 재배포, NFS mount, Promtail 설정은 하지 않는다.
#
# 기본 동작:
# 1. Tomcat이 풀어낸 application.properties 를 찾는다.
# 2. master/slave DB 접속정보와 Gmail 발신 계정 값을 /etc/zzaphub-db.env 로 옮긴다.
# 3. application.properties 에는 ${MASTER_DB_URL}, ${MAIL_PASSWORD} 같은 placeholder만 남긴다.
# 4. tomcat.service systemd drop-in 으로 EnvironmentFile 을 연결한다.
# 5. ROOT.war 가 있으면 WAR 내부 application.properties 도 같은 내용으로 갱신한다.
# 6. Tomcat을 재시작하고 적용 상태를 검증한다.
#
# 실행 예시:
#   sudo bash 'web-secure.patch.sh'
#
# 경로가 다르면:
#   sudo APP_CONTEXT=boot bash 'web-secure.patch.sh'
#   sudo PROP_FILE=/path/application.properties WAR_FILE=/path/ROOT.war bash 'web-secure.patch.sh'
#
# 재실행 안전성:
# - 이미 적용된 항목은 건너뛴다.
# - 기존 파일은 /var/backups/zzaphub-web-secure-patch 아래에 백업한다.
# - 백업 파일에는 기존 secret이 들어 있을 수 있으므로 root만 읽게 권한을 제한한다.

SERVICE_NAME="${SERVICE_NAME:-tomcat.service}"
TOMCAT_HOME="${TOMCAT_HOME:-/opt/tomcat/tomcat-10}"
APP_CONTEXT="${APP_CONTEXT:-ROOT}"

PROP_FILE="${PROP_FILE:-${TOMCAT_HOME}/webapps/${APP_CONTEXT}/WEB-INF/classes/application.properties}"
WAR_FILE="${WAR_FILE:-${TOMCAT_HOME}/webapps/${APP_CONTEXT}.war}"

ENV_FILE="${ENV_FILE:-/etc/zzaphub-db.env}"
DROPIN_DIR="${DROPIN_DIR:-/etc/systemd/system/${SERVICE_NAME}.d}"
DROPIN_FILE="${DROPIN_FILE:-${DROPIN_DIR}/10-zzaphub-db-env.conf}"

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/zzaphub-web-secure-patch}"
RUN_ID="$(date +%Y%m%d-%H%M%S)"

RESTART_TOMCAT="${RESTART_TOMCAT:-1}"
UPDATE_WAR="${UPDATE_WAR:-1}"

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

make_backup_dir() {
    install -d -m 700 -o root -g root "${BACKUP_ROOT}"
}

safe_backup_name() {
    local file_path="$1"
    basename "${file_path}" | tr -c 'A-Za-z0-9._-' '_'
}

backup_file() {
    local file_path="$1"
    local backup_path

    [ -e "${file_path}" ] || return 0

    backup_path="${BACKUP_ROOT}/$(safe_backup_name "${file_path}").${RUN_ID}.bak"
    cp -a "${file_path}" "${backup_path}"
    chown root:root "${backup_path}" 2>/dev/null || true
    chmod 600 "${backup_path}" 2>/dev/null || true

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
    warn "방법 1: 서버 터미널에서 sudo bash 'web-secure.patch.sh' 로 실행해 질문에 답하세요."
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

    master_db_url="${master_db_url:-$(get_property "spring.datasource.master.jdbc-url" "${PROP_FILE}")}"
    master_db_user="${master_db_user:-$(get_property "spring.datasource.master.username" "${PROP_FILE}")}"
    master_db_password="${master_db_password:-$(get_property "spring.datasource.master.password" "${PROP_FILE}")}"
    slave_db_url="${slave_db_url:-$(get_property "spring.datasource.slave.jdbc-url" "${PROP_FILE}")}"
    slave_db_user="${slave_db_user:-$(get_property "spring.datasource.slave.username" "${PROP_FILE}")}"
    slave_db_password="${slave_db_password:-$(get_property "spring.datasource.slave.password" "${PROP_FILE}")}"
    mail_username="${mail_username:-$(get_property "spring.mail.username" "${PROP_FILE}")}"
    mail_password="${mail_password:-$(get_property "spring.mail.password" "${PROP_FILE}")}"
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
        log "기존 env 파일 백업: $(backup_file "${ENV_FILE}")"
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
        die "${ENV_FILE} 에 MASTER_DB_*/SLAVE_DB_* 6개와 MAIL_USERNAME/MAIL_PASSWORD 값을 채울 수 없습니다."
    fi

    log "${ENV_FILE} 을 준비했습니다. secret 값은 출력하지 않습니다."
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

    log "application.properties 백업 생성: $(backup_file "${PROP_FILE}")"

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
    local backup_path=""

    if ! command -v systemctl >/dev/null 2>&1; then
        die "systemctl 을 찾을 수 없습니다. 이 스크립트는 systemd 기반 WEB 서버를 대상으로 합니다."
    fi

    if ! systemctl cat "${SERVICE_NAME}" >/dev/null 2>&1; then
        die "${SERVICE_NAME} 을 찾을 수 없습니다. Tomcat service 이름이 다르면 SERVICE_NAME=... 로 지정하세요."
    fi

    install -d -m 755 -o root -g root "${DROPIN_DIR}"

    if [ -f "${DROPIN_FILE}" ] && grep -Fq "EnvironmentFile=${ENV_FILE}" "${DROPIN_FILE}"; then
        log "systemd drop-in 이 이미 ${ENV_FILE} 을 참조합니다."
        return 0
    fi

    if [ -f "${DROPIN_FILE}" ]; then
        backup_path="$(backup_file "${DROPIN_FILE}")"
        log "기존 systemd drop-in 백업 생성: ${backup_path}"
    fi

    cat > "${DROPIN_FILE}" <<EOF
[Service]
EnvironmentFile=${ENV_FILE}
EOF

    chmod 644 "${DROPIN_FILE}"
    chown root:root "${DROPIN_FILE}" 2>/dev/null || true

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
    local backup_path

    if [ "${UPDATE_WAR}" != "1" ]; then
        warn "UPDATE_WAR=0 이므로 WAR 내부 application.properties 갱신을 건너뜁니다."
        return 0
    fi

    if [ ! -f "${WAR_FILE}" ]; then
        warn "${WAR_FILE} 이 없습니다. 배포된 폴더만 수정했습니다."
        return 0
    fi

    if ! command -v jar >/dev/null 2>&1; then
        warn "jar 명령을 찾을 수 없어 ${WAR_FILE} 갱신을 건너뜁니다. JDK 설치 후 다시 실행하세요."
        return 0
    fi

    backup_path="$(backup_file "${WAR_FILE}")"
    log "WAR 백업 생성: ${backup_path}"

    tmp_dir="$(mktemp -d)"
    mkdir -p "${tmp_dir}/WEB-INF/classes"
    cp "${PROP_FILE}" "${tmp_dir}/WEB-INF/classes/application.properties"

    (
        cd "${tmp_dir}"
        jar uf "${WAR_FILE}" WEB-INF/classes/application.properties
    )

    cleanup_tmp_dir "${tmp_dir}"
    log "WAR 내부 application.properties 도 placeholder 버전으로 갱신했습니다."
}

restart_tomcat_if_requested() {
    if [ "${RESTART_TOMCAT}" != "1" ]; then
        warn "RESTART_TOMCAT=0 이므로 Tomcat 재시작은 하지 않았습니다."
        warn "수동 반영: sudo systemctl daemon-reload && sudo systemctl restart ${SERVICE_NAME}"
        return 0
    fi

    systemctl daemon-reload
    systemctl restart "${SERVICE_NAME}"
    log "Tomcat 재시작 완료: ${SERVICE_NAME}"
}

verify_result() {
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

    env_file_has_all_secure_vars || failed=1
    [ -f "${DROPIN_FILE}" ] && grep -Fq "EnvironmentFile=${ENV_FILE}" "${DROPIN_FILE}" || failed=1

    if [ "${failed}" -ne 0 ]; then
        die "검증 실패. 백업 위치를 확인하세요: ${BACKUP_ROOT}"
    fi

    log "검증 완료: properties placeholder, env 파일, systemd drop-in 이 준비되었습니다."
    log "secret 값은 출력하지 않았습니다."
    log "rollback 참고: ${BACKUP_ROOT} 의 백업 파일을 원래 위치로 복사한 뒤 systemctl daemon-reload/restart 를 수행하세요."
}

main() {
    require_root
    make_backup_dir

    log "WEB DB/Gmail 보안 패치 시작"
    log "대상 properties: ${PROP_FILE}"
    log "대상 env 파일: ${ENV_FILE}"
    log "Tomcat service: ${SERVICE_NAME}"

    [ -f "${PROP_FILE}" ] || die "${PROP_FILE} 을 찾을 수 없습니다. Tomcat이 WAR를 아직 풀지 않았거나 APP_CONTEXT/TOMCAT_HOME 이 다릅니다."

    ensure_secret_env_file
    secure_application_properties
    write_systemd_dropin
    update_war_if_present
    restart_tomcat_if_requested
    verify_result

    log "WEB DB/Gmail secret 하드코딩 제거 작업이 끝났습니다."
}

main "$@"
