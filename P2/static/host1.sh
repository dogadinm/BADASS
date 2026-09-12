#!/bin/sh
set -eu
# Host 1 lives in the overlay LAN. Its address is not part of the router base image.
ip link set eth0 up
ip addr flush dev eth0 || true
ip addr add 192.168.10.1/24 dev eth0
ip addr show eth0
