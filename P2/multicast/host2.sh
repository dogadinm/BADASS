#!/bin/sh
set -eu
ip link set eth0 up
ip addr flush dev eth0 || true
ip addr add 192.168.10.2/24 dev eth0
ip addr show eth0
