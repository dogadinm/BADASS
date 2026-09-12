# P2 validation — 2026-09-12

Command: `sh P2/scripts/check.sh` — **PASS**, exit code 0.
Environment: Docker Desktop on macOS, Linux containers, `linux/amd64`.

Shared images from P1:

- `badass-host:p1`: `ade92c8f5e2d`
- `badass-router:p1`: `85bdacc2fec1`

Passed checks:

- P1 host tools, FRR services/configuration, absence of preset global IPs,
  and router restart/configuration reload.
- Static VXLAN twice, multicast VXLAN twice, then static twice again.
- Underlay reachability and bidirectional host-to-host overlay pings.
- 1450-byte IPv4 packets with fragmentation disabled in both directions.
- VNI 10, UDP 4789, bridge `br0` with access and VXLAN ports.
- Remote host MAC learning on both routers.
- VXLAN packet capture; multicast packets to `239.1.1.1` and group membership.
- Negative check: host connectivity fails with the VXLAN interface down.

The old scripts left host MTU at 1500 while VXLAN used 1450. The earlier
temporary test log showed 1500-byte packets being lost. Host and router
access MTUs now explicitly use 1450 for the 1500-byte IPv4 underlay.

The network test uses four isolated namespaces inside the P1 router image.
P1's actual host image and FRR startup are checked separately by the same
command. This is not a GNS3 GUI/import or four-container integration test.

Still required for submission: create/import and run the P2 topology in the
school Linux VM, verify consoles and stop/start behavior, reapply runtime
scripts after restart, and export `P2.gns3project` with the base images.
No P2 GNS3 export is currently present in this repository.
