#!/bin/sh
set -eu
# Host overlay address; 1450 leaves room for the VXLAN/UDP/IPv4 header.
ip link set eth0 mtu 1450
ip link set eth0 up
ip addr replace 192.168.10.1/24 dev eth0
