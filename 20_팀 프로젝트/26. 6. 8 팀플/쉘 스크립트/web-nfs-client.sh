#!/bin/bash
set -euo pipefail

# Mount a single NFS server on a WEB VM.
#
# Usage:
#   sudo NFS_HOST="NFS_SERVER_IP" bash web-nfs-client.sh
#   sudo bash web-nfs-client.sh NFS_SERVER_IP
#
# Optional:
#   REMOTE_SHARE=/share_directory
#   MOUNT_DIR=/opt/tomcat/tomcat-10/webapps/upload
#   NFS_VERSION=4

NFS_HOST="${NFS_HOST:-${1:-}}"
REMOTE_SHARE="${REMOTE_SHARE:-/share_directory}"
MOUNT_DIR="${MOUNT_DIR:-/opt/tomcat/tomcat-10/webapps/upload}"
NFS_VERSION="${NFS_VERSION:-4}"
BACKUP_BASE="${BACKUP_BASE:-/opt/tomcat}"

[ -n "$NFS_HOST" ] || {
    echo "[ERROR] Set NFS_HOST or pass it as the first argument." >&2
    echo "        Example: sudo NFS_HOST='NFS_SERVER_IP' bash web-nfs-client.sh" >&2
    exit 1
}

EXPECTED_SOURCE="${NFS_HOST}:${REMOTE_SHARE}"
FSTAB_OPTIONS="defaults,_netdev,nofail,vers=${NFS_VERSION},proto=tcp,hard,timeo=50,retrans=2,x-systemd.automount,x-systemd.idle-timeout=30s,x-systemd.device-timeout=5s,x-systemd.mount-timeout=10s"
RUNTIME_OPTIONS="rw,vers=${NFS_VERSION},proto=tcp,hard,timeo=50,retrans=2"
FSTAB_LINE="${EXPECTED_SOURCE} ${MOUNT_DIR} nfs ${FSTAB_OPTIONS} 0 0"

log() {
    echo "[INFO] $*"
}

die() {
    echo "[ERROR] $*" >&2
    exit 1
}

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "Run as root."
    fi
}

mount_sources() {
    findmnt -n -o SOURCE --mountpoint "$MOUNT_DIR" 2>/dev/null | sed '/^[[:space:]]*$/d' || true
}

mount_source_count() {
    mount_sources | wc -l
}

current_mount_source() {
    mount_sources | head -n 1
}

is_mounted() {
    [ "$(mount_source_count)" -gt 0 ]
}

is_expected_source() {
    [ "$1" = "$EXPECTED_SOURCE" ] || [ "$1" = "$EXPECTED_SOURCE/" ]
}

print_mount_status() {
    log "Mount status:"
    findmnt --mountpoint "$MOUNT_DIR" || true
    df -h | grep "$MOUNT_DIR" || true
}

register_fstab() {
    log "Registering NFS mount in /etc/fstab."
    sed -i "\|[[:space:]]${MOUNT_DIR}[[:space:]]|d" /etc/fstab
    echo "$FSTAB_LINE" >> /etc/fstab
    systemctl daemon-reload
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

main() {
    require_root

    log "Installing NFS client tools."
    apt update
    apt install -y nfs-common lsof

    log "Preparing mount point: ${MOUNT_DIR}"
    mkdir -p "$MOUNT_DIR"

    if is_mounted; then
        count="$(mount_source_count)"
        [ "$count" -eq 1 ] || die "${MOUNT_DIR} is mounted multiple times. Unmount manually first."

        source="$(current_mount_source)"
        if is_expected_source "$source"; then
            register_fstab
            timeout 20s mount -o "remount,${RUNTIME_OPTIONS}" "$MOUNT_DIR" || true
            print_mount_status
            log "NFS client setup already applied."
            exit 0
        fi

        die "${MOUNT_DIR} is mounted from unexpected source '${source}', expected '${EXPECTED_SOURCE}'."
    fi

    backup_dir=""
    if find "$MOUNT_DIR" -mindepth 1 -print -quit | grep -q .; then
        backup_dir="${BACKUP_BASE}/upload-local-backup-$(date +%Y%m%d-%H%M%S)"
        log "Backing up existing local upload files to ${backup_dir}."
        mkdir -p "$backup_dir"
        cp -a "${MOUNT_DIR}/." "$backup_dir/"
    fi

    register_fstab

    log "Mounting ${EXPECTED_SOURCE}."
    mount -o "$RUNTIME_OPTIONS" "$EXPECTED_SOURCE" "$MOUNT_DIR"

    if [ -n "$backup_dir" ]; then
        log "Copying local backup into NFS without overwriting existing files."
        copy_backup_without_overwrite "$backup_dir" "$MOUNT_DIR"
    fi

    source="$(current_mount_source)"
    is_expected_source "$source" || die "Mounted source mismatch. Current='${source}', expected='${EXPECTED_SOURCE}'."

    print_mount_status
    log "WEB NFS client setup completed."
}

main "$@"
