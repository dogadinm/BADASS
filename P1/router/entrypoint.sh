#!/bin/bash
set -e

# This path is runtime-only; /etc/frr is the persistent GNS3 configuration.
# A stopped container can retain PID/socket files. They must not be mistaken
# for live daemons when Docker reuses PIDs on the next start.
rm -rf /var/run/frr /var/tmp/frr
mkdir -p /var/run/frr
chown frr:frr /var/run/frr

# Use FRR's own daemon list and supervisor. It starts the selected daemons,
# loads frr.conf and restarts a daemon if it exits unexpectedly.
source /usr/lib/frr/frrcommon.sh
exec /usr/lib/frr/watchfrr $(daemon_list)
