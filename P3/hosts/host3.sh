#!/bin/sh
set -eu
# Start without an IP address; assign 192.168.10.3/24 before the ping stage.
ip link set eth0 mtu 1450
ip link set eth0 up
ip -4 addr flush dev eth0
