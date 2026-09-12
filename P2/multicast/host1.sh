#!/bin/sh
set -eu
# Host 1 lives in the overlay LAN. Its address is not part of the router base image.
# IPv4 VXLAN adds 50 bytes on the 1500-byte underlay.
ip link set eth0 mtu 1450
ip link set eth0 up
ip addr flush dev eth0 || true
ip addr add 192.168.10.1/24 dev eth0
ip addr show eth0
