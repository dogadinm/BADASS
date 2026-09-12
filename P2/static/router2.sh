#!/bin/sh
set -eu
# BADASS P2 - static VXLAN, router 2
UNDERLAY_IF=eth0
ACCESS_IF=eth1
LOCAL_VTEP=10.0.0.2
REMOTE_VTEP=10.0.0.1

ip link set "$UNDERLAY_IF" up
ip link set "$ACCESS_IF" up
ip addr flush dev "$UNDERLAY_IF" || true
ip addr add ${LOCAL_VTEP}/24 dev "$UNDERLAY_IF"

ip link del vxlan10 2>/dev/null || true
ip link del br0 2>/dev/null || true
ip link add br0 type bridge
ip link set br0 up
ip link set "$ACCESS_IF" master br0
ip link add vxlan10 type vxlan id 10 local "$LOCAL_VTEP" remote "$REMOTE_VTEP" dstport 4789 dev "$UNDERLAY_IF"
ip link set vxlan10 up
ip link set vxlan10 master br0

ip -d link show vxlan10
bridge link
bridge fdb show br br0
