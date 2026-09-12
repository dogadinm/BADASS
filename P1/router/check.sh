#!/bin/sh
set -eu
# Check every process and its management socket. Topology-specific protocol
# configuration is checked by scripts/check.sh, so this health check can be
# reused with different P2/P3 configurations.
for daemon in mgmtd zebra bgpd ospfd isisd staticd; do
    test -s "/var/run/frr/$daemon.pid"
    kill -0 "$(cat "/var/run/frr/$daemon.pid")"
    vtysh -d "$daemon" -c 'show version' >/dev/null
done
