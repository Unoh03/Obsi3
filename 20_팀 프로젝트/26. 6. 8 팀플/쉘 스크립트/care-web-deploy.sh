#!/usr/bin/env bash
set -euo pipefail

# Update deploy script for the CARE PHP web server.
#
# Use this after care-web-bootstrap.sh has configured Apache.
#
# What this script does:
#   1. Clone /opt/care-src if missing, otherwise git pull --ff-only.
#   2. Run php -l against every PHP file.
#   3. rsync code to /var/www/html/care while preserving data/.
#   4. Keep code read-only to Apache and keep only data/ writable.
#   5. Reload Apache and run a local HTTP check.
#
# Usage:
#   sudo bash care-web-deploy.sh
#
# Optional overrides:
#   sudo REPO_URL="https://github.com/Unoh03/care.git" bash care-web-deploy.sh
#   sudo BRANCH="main" bash care-web-deploy.sh
#   sudo HEALTH_URL="http://127.0.0.1/" bash care-web-deploy.sh

REPO_URL="${REPO_URL:-https://github.com/Unoh03/care.git}"
BRANCH="${BRANCH:-main}"
SRC="${SRC:-/opt/care-src}"
DEST="${DEST:-/var/www/html/care}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1/}"
WEB_USER="${WEB_USER:-www-data}"
WEB_GROUP="${WEB_GROUP:-www-data}"

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
    echo "[ERROR] missing command: $1" >&2
    echo "[INFO] Run care-web-bootstrap.sh first, or install the missing package." >&2
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
  echo "[1/5] Syncing source repository"

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
  echo "[2/5] Checking PHP syntax"

  local count=0
  while IFS= read -r -d '' file; do
    count=$((count + 1))
    php -l "${file}" >/dev/null
  done < <(find "${SRC}" -type f -name "*.php" -print0)

  echo "[OK] PHP syntax check passed (${count} file(s))."
}

deploy_code() {
  echo "[3/5] Deploying code to Apache DocumentRoot"

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

  echo "[4/5] Fixing permissions"

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

echo "[0/5] Checking required commands"
need_cmd apache2ctl
need_cmd curl
need_cmd git
need_cmd php
need_cmd rsync

sync_source
check_php_syntax
deploy_code

echo "[5/5] Reloading Apache and checking local HTTP"
"${SUDO[@]}" apache2ctl configtest
"${SUDO[@]}" systemctl reload apache2

curl -fsS --max-time 10 -o /dev/null "${HEALTH_URL}"

echo "[OK] CARE deploy complete."
echo "[INFO] Source: ${SRC}"
echo "[INFO] DocumentRoot: ${DEST}"
echo "[INFO] Local check: ${HEALTH_URL}"
echo "[INFO] This script does not configure the database server or firewall."
