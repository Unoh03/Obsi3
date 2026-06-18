#!/usr/bin/env bash
set -euo pipefail

# Initial setup for the CARE PHP web server.
#
# What this script does:
#   1. Install Apache, PHP, mysqli support, git, rsync, and curl.
#   2. Clone or update the CARE GitHub repository under /opt/care-src.
#   3. Configure Apache so /var/www/html/care is the DocumentRoot.
#   4. Deploy code to /var/www/html/care while preserving data/.
#   5. Fix permissions so only data/ is writable by Apache/PHP.
#   6. Reload Apache and run a local HTTP check.
#
# Default access URL after setup:
#   http://WEB_SERVER_IP/
#
# Usage:
#   sudo bash care-web-bootstrap.sh
#
# Optional overrides:
#   sudo REPO_URL="https://github.com/Unoh03/care.git" bash care-web-bootstrap.sh
#   sudo BRANCH="main" bash care-web-bootstrap.sh
#   sudo HEALTH_URL="http://127.0.0.1/" bash care-web-bootstrap.sh

REPO_URL="${REPO_URL:-https://github.com/Unoh03/care.git}"
BRANCH="${BRANCH:-main}"
SRC="${SRC:-/opt/care-src}"
DEST="${DEST:-/var/www/html/care}"
SITE_NAME="${SITE_NAME:-care}"
SITE_CONF="/etc/apache2/sites-available/${SITE_NAME}.conf"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1/}"
WEB_USER="${WEB_USER:-www-data}"
WEB_GROUP="${WEB_GROUP:-www-data}"
DISABLE_DEFAULT_SITE="${DISABLE_DEFAULT_SITE:-1}"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
else
  command -v sudo >/dev/null 2>&1 || {
    echo "[ERROR] Run as root or install sudo." >&2
    exit 1
  }
  SUDO=(sudo)
fi

DEPLOY_USER="${SUDO_USER:-$(id -un)}"
if [[ -z "${DEPLOY_USER}" || "${DEPLOY_USER}" = "root" ]]; then
  DEPLOY_USER="$(id -un)"
fi
DEPLOY_GROUP="$(id -gn "${DEPLOY_USER}" 2>/dev/null || id -gn)"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] missing command after install step: $1" >&2
    exit 1
  }
}

run_as_deploy_user() {
  if [[ "$(id -un)" = "${DEPLOY_USER}" ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo -u "${DEPLOY_USER}" "$@"
  elif command -v runuser >/dev/null 2>&1; then
    runuser -u "${DEPLOY_USER}" -- "$@"
  else
    echo "[ERROR] Cannot switch to deploy user: ${DEPLOY_USER}" >&2
    exit 1
  fi
}

sync_source() {
  echo "[2/7] Syncing source repository"

  if [[ -e "${SRC}" && ! -d "${SRC}/.git" ]]; then
    if [[ -d "${SRC}" && -z "$(find "${SRC}" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
      echo "[WARN] Removing empty non-git source directory from previous failed run: ${SRC}"
      "${SUDO[@]}" rm -rf "${SRC}"
    else
      echo "[ERROR] SRC exists but is not an empty directory or git repository: ${SRC}" >&2
      exit 1
    fi
  fi

  if [[ ! -d "${SRC}/.git" ]]; then
    "${SUDO[@]}" mkdir -p "$(dirname "${SRC}")"
    "${SUDO[@]}" rm -rf "${SRC}"
    "${SUDO[@]}" mkdir -p "${SRC}"
    "${SUDO[@]}" chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${SRC}"
    run_as_deploy_user git clone --branch "${BRANCH}" "${REPO_URL}" "${SRC}"
  else
    "${SUDO[@]}" chown -R "${DEPLOY_USER}:${DEPLOY_GROUP}" "${SRC}"
    run_as_deploy_user git -C "${SRC}" fetch origin "${BRANCH}"
    run_as_deploy_user git -C "${SRC}" checkout "${BRANCH}"
    run_as_deploy_user git -C "${SRC}" pull --ff-only origin "${BRANCH}"
  fi
}

check_php_syntax() {
  echo "[3/7] Checking PHP syntax"

  local count=0
  while IFS= read -r -d '' file; do
    count=$((count + 1))
    php -l "${file}" >/dev/null
  done < <(find "${SRC}" -type f -name "*.php" -print0)

  echo "[OK] PHP syntax check passed (${count} file(s))."
}

deploy_code() {
  echo "[5/7] Deploying code to Apache DocumentRoot"

  "${SUDO[@]}" mkdir -p "${DEST}"

  "${SUDO[@]}" rsync -a --delete \
    --exclude ".git/" \
    --exclude ".gitignore" \
    --exclude ".vscode/" \
    --exclude "data/" \
    --exclude ".env" \
    --exclude "config.local.php" \
    --exclude "*.local.php" \
    --exclude "*.log" \
    "${SRC}/" \
    "${DEST}/"

  echo "[6/7] Fixing permissions"

  "${SUDO[@]}" mkdir -p "${DEST}/data"

  # Code should be readable by Apache, but not writable by the web process.
  "${SUDO[@]}" chown -R root:root "${DEST}"
  "${SUDO[@]}" find "${DEST}" -type d -exec chmod 755 {} +
  "${SUDO[@]}" find "${DEST}" -type f -exec chmod 644 {} +

  # Only runtime upload data should be writable by Apache/PHP.
  "${SUDO[@]}" chown -R "${WEB_USER}:${WEB_GROUP}" "${DEST}/data"
  "${SUDO[@]}" find "${DEST}/data" -type d -exec chmod 775 {} +
  "${SUDO[@]}" find "${DEST}/data" -type f -exec chmod 664 {} +
}

echo "[1/7] Installing web dependencies"
command -v apt-get >/dev/null 2>&1 || {
  echo "[ERROR] This script requires an Ubuntu or Debian host with apt-get." >&2
  exit 1
}

"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y \
  apache2 \
  ca-certificates \
  curl \
  git \
  libapache2-mod-php \
  php \
  php-cli \
  php-mysql \
  rsync

need_cmd apache2ctl
need_cmd curl
need_cmd git
need_cmd php
need_cmd rsync

sync_source
check_php_syntax

echo "[4/7] Configuring Apache site"
"${SUDO[@]}" tee "${SITE_CONF}" >/dev/null <<EOF
<VirtualHost *:80>
    ServerName care.local
    DocumentRoot ${DEST}
    DirectoryIndex index.php index.html

    <Directory ${DEST}>
        Options -Indexes -FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/care_error.log
    CustomLog \${APACHE_LOG_DIR}/care_access.log combined
</VirtualHost>
EOF

"${SUDO[@]}" a2enmod rewrite >/dev/null
"${SUDO[@]}" a2ensite "${SITE_NAME}.conf" >/dev/null
if [[ "${DISABLE_DEFAULT_SITE}" = "1" ]]; then
  "${SUDO[@]}" a2dissite 000-default.conf >/dev/null 2>&1 || true
fi

deploy_code

echo "[7/7] Reloading Apache and checking local HTTP"
"${SUDO[@]}" apache2ctl configtest
"${SUDO[@]}" systemctl enable --now apache2
"${SUDO[@]}" systemctl reload apache2

curl -fsS --max-time 10 -o /dev/null "${HEALTH_URL}"

echo "[OK] CARE web server setup complete."
echo "[INFO] Source: ${SRC}"
echo "[INFO] DocumentRoot: ${DEST}"
echo "[INFO] Local check: ${HEALTH_URL}"
echo "[INFO] This script does not configure the database server or firewall."
