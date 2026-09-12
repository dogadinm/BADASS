#!/bin/sh
set -eu
# IPv4 VXLAN adds 50 bytes on the 1500-byte underlay.
ip link set eth0 mtu 1450
ip link set eth0 up
ip addr flush dev eth0 || true
ip addr add 192.168.10.2/24 dev eth0
ip addr show eth0
