#!/usr/bin/env bash
set -euo pipefail
umask 077

# Install a MariaDB client, verify access to RDS, update the deployed
# application.properties file, and restart Tomcat.
# This script does not install a MariaDB server or change AWS security groups.

RDS_PORT="${RDS_PORT:-3306}"
DB_NAME="${DB_NAME:-care}"
DB_USER="${DB_USER:-web}"
PROP_FILE="${PROP_FILE:-/opt/tomcat/current/webapps/boot/WEB-INF/classes/application.properties}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/tomcat}"
RDS_CA_URL="${RDS_CA_URL:-https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem}"
RDS_CA_FILE="${RDS_CA_FILE:-/opt/tomcat/rds-global-bundle.pem}"

die() {
  echo "[ERROR] $*" >&2
  exit 1
}

escape_option_value() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s' "${value}"
}

escape_property_value() {
  local value="$1"
  value="${value//\\/\\\\}"

  while [[ "${value}" == " "* ]]; do
    value="\\ ${value:1}"
  done

  printf '%s' "${value}"
}

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
else
  command -v sudo >/dev/null 2>&1 || die "Run this script as root or install sudo."
  SUDO=(sudo)
fi

command -v apt-get >/dev/null 2>&1 || die "This script requires an Ubuntu or Debian host with apt-get."
command -v systemctl >/dev/null 2>&1 || die "systemctl was not found."

if [[ -z "${RDS_ENDPOINT:-}" ]]; then
  read -r -p "[INPUT] RDS endpoint: " RDS_ENDPOINT
fi

read -r -p "[INPUT] Database name [${DB_NAME}]: " INPUT_DB_NAME
DB_NAME="${INPUT_DB_NAME:-${DB_NAME}}"

read -r -p "[INPUT] Application DB user [${DB_USER}]: " INPUT_DB_USER
DB_USER="${INPUT_DB_USER:-${DB_USER}}"

read -r -s -p "[INPUT] Password for ${DB_USER}: " DB_PASSWORD
echo

[[ "${RDS_ENDPOINT}" =~ ^[A-Za-z0-9.-]+$ ]] || die "RDS endpoint contains unsupported characters."
[[ "${RDS_PORT}" =~ ^[0-9]+$ ]] || die "RDS port must be numeric."
[[ "${DB_NAME}" =~ ^[A-Za-z0-9_]+$ ]] || die "Database name contains unsupported characters."
[[ "${DB_USER}" =~ ^[A-Za-z0-9_.-]+$ ]] || die "Database user contains unsupported characters."
[[ -n "${DB_PASSWORD}" ]] || die "Database password must not be empty."

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "[INFO] Installing MariaDB client tools..."
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y mariadb-client netcat-openbsd curl

echo "[INFO] Checking TCP access to ${RDS_ENDPOINT}:${RDS_PORT}..."
if ! nc -z -w 5 "${RDS_ENDPOINT}" "${RDS_PORT}"; then
  die "RDS port is unreachable. Allow TCP ${RDS_PORT} from the EC2 security group in the RDS security group."
fi

CLIENT_CNF="${TMP_DIR}/client.cnf"
cat > "${CLIENT_CNF}" <<EOF
[client]
host="$(escape_option_value "${RDS_ENDPOINT}")"
port="${RDS_PORT}"
user="$(escape_option_value "${DB_USER}")"
password="$(escape_option_value "${DB_PASSWORD}")"
database="$(escape_option_value "${DB_NAME}")"
EOF

echo "[INFO] Verifying the ${DB_USER} account and ${DB_NAME} database..."
if ! mariadb \
  --defaults-extra-file="${CLIENT_CNF}" \
  --connect-timeout=5 \
  --batch \
  --skip-column-names \
  --execute='SELECT 1;' \
  >/dev/null; then
  die "RDS login failed. Check the web account host, password, database, and GRANT settings."
fi

echo "[OK] RDS login succeeded."

id -u tomcat >/dev/null 2>&1 || die "The tomcat service account was not found. Run ec2_tomcat_setup.sh first."

echo "[INFO] Installing the Amazon RDS CA bundle..."
curl --fail --silent --show-error --location \
  --output "${TMP_DIR}/global-bundle.pem" \
  "${RDS_CA_URL}"
"${SUDO[@]}" install \
  --mode 0640 \
  --owner root \
  --group tomcat \
  "${TMP_DIR}/global-bundle.pem" \
  "${RDS_CA_FILE}"

for _ in {1..60}; do
  if "${SUDO[@]}" test -f "${PROP_FILE}"; then
    break
  fi

  sleep 1
done

"${SUDO[@]}" test -f "${PROP_FILE}" || die "application.properties was not found: ${PROP_FILE}"

JDBC_URL="jdbc:mariadb://${RDS_ENDPOINT}:${RDS_PORT}/${DB_NAME}?sslMode=verify-full&serverSslCert=${RDS_CA_FILE}"
PROP_URL="$(escape_property_value "${JDBC_URL}")"
PROP_USER="$(escape_property_value "${DB_USER}")"
PROP_PASSWORD="$(escape_property_value "${DB_PASSWORD}")"
TMP_PROPERTIES="${TMP_DIR}/application.properties"

rewrite_properties() {
  local found_url=0
  local found_user=0
  local found_password=0
  local line

  while IFS= read -r line || [[ -n "${line}" ]]; do
    case "${line}" in
      spring.datasource.url=*|spring.datasource.url:*)
        printf 'spring.datasource.url=%s\n' "${PROP_URL}"
        found_url=1
        ;;
      spring.datasource.username=*|spring.datasource.username:*)
        printf 'spring.datasource.username=%s\n' "${PROP_USER}"
        found_user=1
        ;;
      spring.datasource.password=*|spring.datasource.password:*)
        printf 'spring.datasource.password=%s\n' "${PROP_PASSWORD}"
        found_password=1
        ;;
      *)
        printf '%s\n' "${line}"
        ;;
    esac
  done

  [[ "${found_url}" -eq 1 ]] || printf 'spring.datasource.url=%s\n' "${PROP_URL}"
  [[ "${found_user}" -eq 1 ]] || printf 'spring.datasource.username=%s\n' "${PROP_USER}"
  [[ "${found_password}" -eq 1 ]] || printf 'spring.datasource.password=%s\n' "${PROP_PASSWORD}"
}

echo "[INFO] Backing up and updating ${PROP_FILE}..."
"${SUDO[@]}" install -d --mode 0700 --owner root --group root "${BACKUP_DIR}"
BACKUP_FILE="${BACKUP_DIR}/application.properties.$(date +%Y%m%d-%H%M%S).bak"
"${SUDO[@]}" cp "${PROP_FILE}" "${BACKUP_FILE}"
"${SUDO[@]}" chown root:root "${BACKUP_FILE}"
"${SUDO[@]}" chmod 0600 "${BACKUP_FILE}"

rewrite_properties < <("${SUDO[@]}" cat "${PROP_FILE}") > "${TMP_PROPERTIES}"
"${SUDO[@]}" install \
  --mode 0640 \
  --owner tomcat \
  --group tomcat \
  "${TMP_PROPERTIES}" \
  "${PROP_FILE}"

echo "[INFO] Restarting Tomcat..."
"${SUDO[@]}" systemctl restart tomcat

PORT_OPEN=0
for _ in {1..30}; do
  if ! "${SUDO[@]}" systemctl is-active --quiet tomcat; then
    break
  fi

  if "${SUDO[@]}" ss -lnt | grep -q ':8080 '; then
    PORT_OPEN=1
    break
  fi

  sleep 1
done

if ! "${SUDO[@]}" systemctl is-active --quiet tomcat; then
  echo "[ERROR] Tomcat did not restart. Recent logs:" >&2
  "${SUDO[@]}" journalctl --unit tomcat --no-pager --lines 50 >&2
  exit 1
fi

[[ "${PORT_OPEN}" -eq 1 ]] || die "Tomcat is active, but TCP port 8080 was not detected within 30 seconds."

echo "[OK] Tomcat is listening on TCP port 8080."
if curl --fail --silent --show-error --max-time 10 \
  --output /dev/null \
  http://127.0.0.1:8080/boot/; then
  echo "[OK] The local boot application responded."
else
  echo "[WARN] Tomcat is listening, but the boot application did not respond successfully."
  echo "[INFO] Check logs with: sudo journalctl -u tomcat -n 100 --no-pager"
fi

echo "[OK] application.properties was updated."
echo "[INFO] Backup: ${BACKUP_FILE}"
echo "[WARN] The DB password is stored in plaintext in ${PROP_FILE}."
echo "[WARN] Redeploying boot.war can overwrite this file. Re-run this script after a redeploy."
