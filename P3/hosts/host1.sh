#!/bin/sh
set -eu
# Start without an IP address so EVPN can demonstrate MAC-only type-2 learning.
# Assign 192.168.10.1/24 after the MAC-only stage of the evaluation.
ip link set eth0 mtu 1450
ip link set eth0 up
ip -4 addr flush dev eth0
