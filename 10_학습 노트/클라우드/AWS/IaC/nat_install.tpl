#!/bin/bash

echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.d/99-custom-nat.conf
sudo sysctl -p /etc/sysctl.d/99-custom-nat.conf
IFACE=$(ip route show default | awk '/default/ {print $5}')
sudo iptables -t nat -A POSTROUTING -o $IFACE -j MASQUERADE