#!/bin/sh
set -eu
# Runtime addresses belong to this project, never to the base image.
ip link set lo up
ip addr replace 1.1.1.3/32 dev lo
# The central router forwards VXLAN packets between the leaves.
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w net.ipv4.conf.default.rp_filter=0
ip link set eth0 up
ip addr replace 10.1.1.6/30 dev eth0
ip link set eth1 mtu 1450
ip link set eth1 up
# Recreate only the lab bridge/tunnel. FRR installs remote FDB entries.
ip link del vxlan10 2>/dev/null || true
ip link del br0 2>/dev/null || true
ip link add br0 type bridge
ip link set br0 address 02:42:00:03:00:03 addrgenmode none
ip link add vxlan10 type vxlan id 10 local 1.1.1.3 dstport 4789 nolearning
ip link set vxlan10 mtu 1450 master br0 addrgenmode none
# Disable data-plane learning on the tunnel; EVPN provides remote MACs.
bridge link set dev vxlan10 learning off
ip link set eth1 master br0
ip link set br0 mtu 1450 up
ip link set vxlan10 up
# L2-only overlay: no gateway IP or IP forwarding on the bridge.
sysctl -w net.ipv4.conf.br0.forwarding=0
sysctl -w net.ipv6.conf.br0.forwarding=0
