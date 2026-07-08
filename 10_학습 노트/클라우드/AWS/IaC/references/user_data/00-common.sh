#!/bin/bash
set -euo pipefail

SWAP_FILE="/swapfile"
SWAP_SIZE="2G"

if ! swapon --show=NAME | grep -qx "$SWAP_FILE"; then
    if [[ ! -f "$SWAP_FILE" ]]; then
    fallocate -l "$SWAP_SIZE" "$SWAP_FILE" || dd if=/dev/zero of="$SWAP_FILE" bs=1M count=2048
    fi

    chmod 600 "$SWAP_FILE"
    mkswap "$SWAP_FILE"
    swapon "$SWAP_FILE"
fi

grep -qxF "$SWAP_FILE none swap sw 0 0" /etc/fstab || echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab

echo 'vm.swappiness = 10' > /etc/sysctl.d/99-low-memory-lab.conf
sysctl --system >/dev/null