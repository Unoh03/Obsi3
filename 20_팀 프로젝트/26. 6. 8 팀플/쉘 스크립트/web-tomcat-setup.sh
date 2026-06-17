#!/usr/bin/env bash
set -euo pipefail

# Install Tomcat and deploy a WAR on a WEB VM.
# This script does not change application properties, firewall rules, NFS, DB,
# Redis, mail, or monitoring settings.
#
# Default:
#   - expects boot.war in the invoking user's home directory
#   - deploys it as /boot
#
# Usage:
#   sudo bash web-tomcat-setup.sh
#   sudo APP_CONTEXT=ROOT WAR_SOURCE=/home/ubuntu/app.war bash web-tomcat-setup.sh
#   sudo APP_CONTEXT=myapp WAR_NAME=myapp.war bash web-tomcat-setup.sh

TOMCAT_VERSION="${TOMCAT_VERSION:-10.1.55}"
TOMCAT_USER="${TOMCAT_USER:-tomcat}"
TOMCAT_GROUP="${TOMCAT_GROUP:-tomcat}"
TOMCAT_BASE="${TOMCAT_BASE:-/opt/tomcat}"
TOMCAT_INSTALL_DIR="${TOMCAT_BASE}/apache-tomcat-${TOMCAT_VERSION}"
TOMCAT_CURRENT="${TOMCAT_BASE}/current"
TOMCAT_ARCHIVE="apache-tomcat-${TOMCAT_VERSION}.tar.gz"
TOMCAT_URL="${TOMCAT_URL:-https://archive.apache.org/dist/tomcat/tomcat-10/v${TOMCAT_VERSION}/bin/${TOMCAT_ARCHIVE}}"
SERVICE_NAME="${SERVICE_NAME:-tomcat.service}"
APP_CONTEXT="${APP_CONTEXT:-boot}"
DEPLOY_CLEAN="${DEPLOY_CLEAN:-1}"

case "${APP_CONTEXT}" in
  ""|*/*)
    echo "[ERROR] APP_CONTEXT must be a single Tomcat context name, for example boot, ROOT, or myapp." >&2
    exit 1
    ;;
esac

if [[ -z "${WAR_NAME:-}" ]]; then
  WAR_NAME="${APP_CONTEXT}.war"
fi

case "${WAR_NAME}" in
  *.war)
    ;;
  *)
    echo "[ERROR] WAR_NAME must end with .war: ${WAR_NAME}" >&2
    exit 1
    ;;
esac

SOURCE_HOME="${HOME}"
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  SOURCE_HOME="$(getent passwd "${SUDO_USER}" | cut -d: -f6)"
fi

WAR_SOURCE="${WAR_SOURCE:-${SOURCE_HOME}/${WAR_NAME}}"
WAR_TARGET="${TOMCAT_CURRENT}/webapps/${WAR_NAME}"
EXPANDED_TARGET="${TOMCAT_CURRENT}/webapps/${APP_CONTEXT}"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
else
  command -v sudo >/dev/null 2>&1 || {
    echo "[ERROR] Run this script as root or install sudo." >&2
    exit 1
  }
  SUDO=(sudo)
fi

command -v apt-get >/dev/null 2>&1 || {
  echo "[ERROR] This script requires an Ubuntu or Debian host with apt-get." >&2
  exit 1
}

while [[ ! -f "${WAR_SOURCE}" ]]; do
  echo "[ACTION] WAR file was not found: ${WAR_SOURCE}"
  echo "[ACTION] Upload ${WAR_NAME} to that path, then press Enter to retry."

  if [[ ! -t 0 ]]; then
    echo "[ERROR] Interactive input is required while the WAR file is missing." >&2
    exit 1
  fi

  read -r -p "[WAIT] Press Enter after uploading the WAR file: " _
done

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "[INFO] Installing Java 17 and download tools..."
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y openjdk-17-jdk-headless ca-certificates curl tar

JAVA_BIN="$(readlink -f "$(command -v java)")"
JAVA_HOME="$(dirname "$(dirname "${JAVA_BIN}")")"

if ! id -u "${TOMCAT_USER}" >/dev/null 2>&1; then
  echo "[INFO] Creating the ${TOMCAT_USER} service account..."
  tomcat_shell="/usr/sbin/nologin"
  [[ -x "${tomcat_shell}" ]] || tomcat_shell="/bin/false"

  "${SUDO[@]}" useradd \
    --system \
    --create-home \
    --user-group \
    --home-dir "${TOMCAT_BASE}" \
    --shell "${tomcat_shell}" \
    "${TOMCAT_USER}"
fi

"${SUDO[@]}" mkdir -p "${TOMCAT_BASE}"

if [[ ! -d "${TOMCAT_INSTALL_DIR}" ]]; then
  echo "[INFO] Downloading Apache Tomcat ${TOMCAT_VERSION}..."
  curl --fail --location --retry 3 \
    --output "${TMP_DIR}/${TOMCAT_ARCHIVE}" \
    "${TOMCAT_URL}"

  echo "[INFO] Extracting Apache Tomcat..."
  "${SUDO[@]}" tar -xzf "${TMP_DIR}/${TOMCAT_ARCHIVE}" -C "${TOMCAT_BASE}"
fi

"${SUDO[@]}" chown -R "${TOMCAT_USER}:${TOMCAT_GROUP}" "${TOMCAT_INSTALL_DIR}"
"${SUDO[@]}" find "${TOMCAT_INSTALL_DIR}/bin" \
  -maxdepth 1 \
  -type f \
  -name '*.sh' \
  -exec chmod +x {} +
"${SUDO[@]}" ln -sfn "${TOMCAT_INSTALL_DIR}" "${TOMCAT_CURRENT}"
"${SUDO[@]}" mkdir -p "${TOMCAT_CURRENT}/webapps"

echo "[INFO] Registering the systemd service..."
"${SUDO[@]}" tee "/etc/systemd/system/${SERVICE_NAME}" >/dev/null <<EOF
[Unit]
Description=Apache Tomcat 10 servlet container
After=network.target

[Service]
Type=simple
User=${TOMCAT_USER}
Group=${TOMCAT_GROUP}
Environment=JAVA_HOME=${JAVA_HOME}
Environment=CATALINA_HOME=${TOMCAT_CURRENT}
Environment=CATALINA_BASE=${TOMCAT_CURRENT}
ExecStart=${TOMCAT_CURRENT}/bin/catalina.sh run
ExecStop=/bin/kill -15 \$MAINPID
SuccessExitStatus=143
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

"${SUDO[@]}" systemctl daemon-reload

if "${SUDO[@]}" systemctl is-active --quiet "${SERVICE_NAME}"; then
  echo "[INFO] Stopping ${SERVICE_NAME} before deployment..."
  "${SUDO[@]}" systemctl stop "${SERVICE_NAME}"
fi

if [[ "${DEPLOY_CLEAN}" = "1" ]]; then
  echo "[INFO] Cleaning previous deployment for context ${APP_CONTEXT}..."
  for path in "${WAR_TARGET}" "${EXPANDED_TARGET}"; do
    case "${path}" in
      "${TOMCAT_CURRENT}/webapps/"*)
        "${SUDO[@]}" rm -rf -- "${path}"
        ;;
      *)
        echo "[ERROR] Refusing to remove unexpected deployment path: ${path}" >&2
        exit 1
        ;;
    esac
  done
fi

echo "[INFO] Deploying ${WAR_SOURCE} to ${WAR_TARGET}..."
"${SUDO[@]}" install \
  --mode 0644 \
  --owner "${TOMCAT_USER}" \
  --group "${TOMCAT_GROUP}" \
  "${WAR_SOURCE}" \
  "${WAR_TARGET}"

"${SUDO[@]}" systemctl enable "${SERVICE_NAME}"
"${SUDO[@]}" systemctl restart "${SERVICE_NAME}"

PORT_OPEN=0
for _ in {1..30}; do
  if ! "${SUDO[@]}" systemctl is-active --quiet "${SERVICE_NAME}"; then
    break
  fi

  if "${SUDO[@]}" ss -lnt | grep -q ':8080 '; then
    PORT_OPEN=1
    break
  fi

  sleep 1
done

if ! "${SUDO[@]}" systemctl is-active --quiet "${SERVICE_NAME}"; then
  echo "[ERROR] Tomcat did not start. Recent logs:" >&2
  "${SUDO[@]}" journalctl --unit "${SERVICE_NAME}" --no-pager --lines 50 >&2
  exit 1
fi

if [[ "${APP_CONTEXT}" = "ROOT" ]]; then
  APP_PATH="/"
else
  APP_PATH="/${APP_CONTEXT}/"
fi

echo "[OK] Tomcat is active."
if [[ "${PORT_OPEN}" -eq 1 ]]; then
  echo "[OK] Tomcat is listening on TCP port 8080."
else
  echo "[WARN] Tomcat is active, but TCP port 8080 was not detected within 30 seconds."
  echo "[INFO] Check logs with: sudo journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
fi

if command -v curl >/dev/null 2>&1; then
  if curl --fail --silent --show-error --max-time 5 "http://127.0.0.1:8080${APP_PATH}" >/dev/null; then
    echo "[OK] Local HTTP check succeeded: http://127.0.0.1:8080${APP_PATH}"
  else
    echo "[WARN] Local HTTP check failed: http://127.0.0.1:8080${APP_PATH}"
    echo "[INFO] Check logs with: sudo journalctl -u ${SERVICE_NAME} -n 100 --no-pager"
  fi
fi

echo "[OK] ${WAR_SOURCE} was copied to ${WAR_TARGET}."
echo "[INFO] The original WAR remains at ${WAR_SOURCE}."
echo "[INFO] This script did not change application properties, firewall rules, NFS, DB, Redis, mail, or monitoring settings."
echo "[INFO] Open TCP 8080 or put this WEB VM behind the load balancer separately."
