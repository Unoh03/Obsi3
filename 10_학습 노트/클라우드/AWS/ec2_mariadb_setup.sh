#!/usr/bin/env bash
set -euo pipefail

# Install MariaDB on an EC2 host and prepare the care database for the web app.
# This script changes MariaDB bind-address, but it does not change EC2 security groups.

DB_NAME="${DB_NAME:-care}"
DB_APP_USER="${DB_APP_USER:-web}"
DB_APP_HOST="${DB_APP_HOST:-%}"
DB_BIND_ADDRESS="${DB_BIND_ADDRESS:-0.0.0.0}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-}"
DB_APP_PASSWORD="${DB_APP_PASSWORD:-}"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
else
  command -v sudo >/dev/null 2>&1 || {
    echo "[ERROR] Run this script as root or install sudo." >&2
    exit 1
  }
  SUDO=(sudo)
fi

prompt_secret() {
  local var_name="$1"
  local prompt="$2"
  local value=""

  if [[ ! -t 0 ]]; then
    echo "[ERROR] ${var_name} is required in non-interactive mode." >&2
    echo "[INFO] Example: ${var_name}='<password>' sudo -E ./ec2_mariadb_setup.sh" >&2
    exit 1
  fi

  while [[ -z "${value}" ]]; do
    read -r -s -p "${prompt}: " value
    echo
  done

  printf -v "${var_name}" '%s' "${value}"
}

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

if [[ -z "${DB_ROOT_PASSWORD}" ]]; then
  prompt_secret DB_ROOT_PASSWORD "[INPUT] New MariaDB root password"
fi

if [[ -z "${DB_APP_PASSWORD}" ]]; then
  prompt_secret DB_APP_PASSWORD "[INPUT] Password for '${DB_APP_USER}'@'${DB_APP_HOST}'"
fi

DB_ROOT_PASSWORD_SQL="$(sql_escape "${DB_ROOT_PASSWORD}")"
DB_APP_PASSWORD_SQL="$(sql_escape "${DB_APP_PASSWORD}")"

if command -v apt-get >/dev/null 2>&1; then
  OS_FAMILY="debian"
elif command -v dnf >/dev/null 2>&1; then
  OS_FAMILY="rhel"
elif command -v yum >/dev/null 2>&1; then
  OS_FAMILY="rhel"
else
  echo "[ERROR] This script requires apt-get, dnf, or yum." >&2
  exit 1
fi

echo "[INFO] Installing MariaDB server and client..."
if [[ "${OS_FAMILY}" == "debian" ]]; then
  "${SUDO[@]}" apt-get update
  "${SUDO[@]}" apt-get install -y mariadb-server mariadb-client
else
  if command -v dnf >/dev/null 2>&1; then
    "${SUDO[@]}" dnf install -y mariadb105-server mariadb105
  else
    "${SUDO[@]}" yum install -y mariadb105-server mariadb105
  fi
fi

"${SUDO[@]}" systemctl enable --now mariadb

if [[ "${OS_FAMILY}" == "debian" ]]; then
  MARIADB_BIND_DROPIN="/etc/mysql/mariadb.conf.d/99-ec2-bind.cnf"
else
  MARIADB_BIND_DROPIN="/etc/my.cnf.d/99-ec2-bind.cnf"
fi

echo "[INFO] Setting MariaDB bind-address to ${DB_BIND_ADDRESS}..."
"${SUDO[@]}" tee "${MARIADB_BIND_DROPIN}" >/dev/null <<EOF
[mysqld]
bind-address = ${DB_BIND_ADDRESS}
EOF

SQL_FILE="$(mktemp)"
trap 'rm -f "${SQL_FILE}"' EXIT

cat >"${SQL_FILE}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE \`${DB_NAME}\`;

CREATE TABLE IF NOT EXISTS member (
  id varchar(20) NOT NULL,
  pw varchar(200),
  username varchar(99),
  postcode varchar(5),
  address varchar(1000),
  detailaddress varchar(100),
  mobile varchar(15),
  PRIMARY KEY (id)
) DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS board (
  no int NOT NULL,
  title varchar(200),
  content varchar(9999),
  id varchar(20),
  writedate varchar(100),
  hits int(11),
  filename varchar(1000),
  PRIMARY KEY (no)
) DEFAULT CHARSET=utf8mb4;

CREATE USER IF NOT EXISTS '${DB_APP_USER}'@'${DB_APP_HOST}' IDENTIFIED BY '${DB_APP_PASSWORD_SQL}';
ALTER USER '${DB_APP_USER}'@'${DB_APP_HOST}' IDENTIFIED BY '${DB_APP_PASSWORD_SQL}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_APP_USER}'@'${DB_APP_HOST}';

ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASSWORD_SQL}';
FLUSH PRIVILEGES;
SQL

echo "[INFO] Creating database, tables, and application user..."
"${SUDO[@]}" mariadb -uroot <"${SQL_FILE}"

"${SUDO[@]}" systemctl restart mariadb

echo "[OK] MariaDB is active."
echo "[OK] Database '${DB_NAME}' and user '${DB_APP_USER}'@'${DB_APP_HOST}' are ready."
echo "[INFO] This script did not change EC2 security groups."
echo "[INFO] Allow TCP 3306 from the web server private IP or security group separately."
