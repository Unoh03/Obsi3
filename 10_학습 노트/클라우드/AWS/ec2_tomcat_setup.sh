#!/usr/bin/env bash
set -euo pipefail

# Install Tomcat and deploy boot.war from the invoking user's home directory.
# This script does not change application properties or firewall rules.

TOMCAT_VERSION="${TOMCAT_VERSION:-10.1.55}"
TOMCAT_USER="tomcat"
TOMCAT_GROUP="tomcat"
TOMCAT_BASE="/opt/tomcat"
TOMCAT_INSTALL_DIR="${TOMCAT_BASE}/apache-tomcat-${TOMCAT_VERSION}"
TOMCAT_CURRENT="${TOMCAT_BASE}/current"
TOMCAT_ARCHIVE="apache-tomcat-${TOMCAT_VERSION}.tar.gz"
TOMCAT_URL="https://archive.apache.org/dist/tomcat/tomcat-10/v${TOMCAT_VERSION}/bin/${TOMCAT_ARCHIVE}"
SOURCE_HOME="${HOME}"

if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  SOURCE_HOME="$(getent passwd "${SUDO_USER}" | cut -d: -f6)"
fi

WAR_SOURCE="${WAR_SOURCE:-${SOURCE_HOME}/boot.war}"
WAR_TARGET="${TOMCAT_CURRENT}/webapps/boot.war"

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
  echo "[ACTION] boot.war was not found: ${WAR_SOURCE}"
  echo "[ACTION] Upload boot.war to that path, then press Enter to retry."

  if [[ ! -t 0 ]]; then
    echo "[ERROR] Interactive input is required while boot.war is missing." >&2
    exit 1
  fi

  read -r -p "[WAIT] Press Enter after uploading boot.war: " _
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
  "${SUDO[@]}" useradd \
    --system \
    --create-home \
    --user-group \
    --home-dir "${TOMCAT_BASE}" \
    --shell /usr/sbin/nologin \
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

echo "[INFO] Deploying ${WAR_SOURCE}..."
"${SUDO[@]}" install \
  --mode 0644 \
  --owner "${TOMCAT_USER}" \
  --group "${TOMCAT_GROUP}" \
  "${WAR_SOURCE}" \
  "${WAR_TARGET}"

echo "[INFO] Registering the systemd service..."
"${SUDO[@]}" tee /etc/systemd/system/tomcat.service >/dev/null <<EOF
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
"${SUDO[@]}" systemctl enable tomcat
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
  echo "[ERROR] Tomcat did not start. Recent logs:" >&2
  "${SUDO[@]}" journalctl --unit tomcat --no-pager --lines 50 >&2
  exit 1
fi

echo "[OK] Tomcat is active."
if [[ "${PORT_OPEN}" -eq 1 ]]; then
  echo "[OK] Tomcat is listening on TCP port 8080."
else
  echo "[WARN] Tomcat is active, but TCP port 8080 was not detected within 30 seconds."
  echo "[INFO] Check logs with: sudo journalctl -u tomcat -n 50 --no-pager"
fi

echo "[OK] boot.war was copied to ${WAR_TARGET}."
echo "[INFO] The original boot.war remains at ${WAR_SOURCE}."
echo "[INFO] This script did not change application properties or firewall rules."
echo "[INFO] To test from a browser, allow TCP 8080 separately in the EC2 security group."
