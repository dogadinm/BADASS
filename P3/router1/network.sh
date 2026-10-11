#!/bin/sh
set -eu
# Runtime addresses belong to this project, never to the base image.
ip link set lo up
ip addr replace 1.1.1.1/32 dev lo
# The central router forwards VXLAN packets between the leaves.
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w net.ipv4.conf.default.rp_filter=0
ip link set eth0 up
ip addr replace 10.1.1.1/30 dev eth0
ip link set eth1 up
ip addr replace 10.1.1.5/30 dev eth1
ip link set eth2 up
ip addr replace 10.1.1.9/30 dev eth2
