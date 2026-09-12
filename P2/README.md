# BADASS — P2: Discovering a VXLAN

This directory prepares both required P2 variants: a **static VXLAN** and a **dynamic multicast VXLAN**. The subject requires **VNI 10**, a Linux bridge named **`br0`**, configuration files with comments, and consistent equipment names containing a group member's login.

## GNS3 topology

Build this topology with the [P1 Docker images](../P1/README.md):

`host_dogadinm-1 -- router_dogadinm-1 -- Ethernet switch -- router_dogadinm-2 -- host_dogadinm-2`

Use `badass-host:p1` for both hosts (one adapter, start command `/bin/sh`)
and `badass-router:p1` for both routers (three adapters as in P1, start
command `/usr/local/bin/router-start`; the third adapter is unused).
Connect host `eth0` to its router's `eth1`, and each router's `eth0` to the
switch. P1's original two-node project stays separate; these are four new
nodes in a P2 GNS3 project using the same images.

Each router needs two Ethernet interfaces: `eth0` toward the shared underlay switch and `eth1` toward its local host. If GNS3 assigns different names, edit `UNDERLAY_IF` and `ACCESS_IF` in the scripts.

Address plan used by these scripts:

| Node | Interface | Address / purpose |
|---|---|---|
| router 1 | eth0 | `10.0.0.1/24` (VTEP underlay) |
| router 2 | eth0 | `10.0.0.2/24` (VTEP underlay) |
| host 1 | eth0 | `192.168.10.1/24` (overlay) |
| host 2 | eth0 | `192.168.10.2/24` (overlay) |
| VXLAN | vxlan10 | VNI `10`, UDP `4789` |
| bridge | br0 | bridges `eth1` and `vxlan10` |

The hosts are in the same L2 overlay subnet even though their frames cross the IP underlay between the two VTEPs.

The host and router access interfaces use MTU **1450** to match VXLAN over
the 1500-byte IPv4 underlay. Test a full-size overlay packet with
`ping -c 3 -M do -s 1422 192.168.10.2` from host 1.

## Automated P1 → P2 check

Latest checked behavior and remaining GNS3 steps: [VALIDATION.md](VALIDATION.md).

From the repository root, load or build P1's images, then run:

```sh
# Choose one:
python3 P1/scripts/load-images.py
# sh P1/scripts/build.sh

sh P2/scripts/check.sh
```

The check first runs P1's host and FRR/restart checks. It then mounts this
directory read-only into the P1 router image and creates four network
namespaces connected by veth links and an underlay bridge. It verifies both
VXLAN modes, repeated configuration, switching modes in both directions,
bidirectional pings, 1450-byte packets, learned remote host MACs, VNI 10,
UDP 4789, multicast membership/traffic, and failure when the tunnel is down.
The disposable container and its anonymous volume are removed on exit.
Docker's Linux kernel must support network namespaces, bridges and VXLAN;
the network test container uses `--privileged` and `--network none`.

This validates P2 scripts with P1's networking tools. The four namespaces
share the router image; they are not four GNS3 containers with running FRR.
GNS3 import, console access and school VM validation remain separate checks.

## 1. Static VXLAN

Scripts are in Git, not baked into the P1 images. Open each node's
**Auxiliary console**, run `exec /bin/sh`, then paste the contents of its
matching `P2/static/*.sh` file. Alternatively, copy that file into the node
before running the commands below. For multicast use `P2/multicast/*.sh`.

Run the matching scripts in each GNS3 console (or copy/paste their commands):

```sh
# router 1
sh router1.sh
# router 2
sh router2.sh
# host 1
sh host1.sh
# host 2
sh host2.sh
```

The static scripts configure each VTEP with the other VTEP as its explicit `remote` endpoint.

Verify:

```sh
# host 1
ping 192.168.10.2

# either router
ip -d link show vxlan10
bridge link
bridge fdb show br br0

# capture VXLAN traffic on the underlay
# (use the actual underlay interface if not eth0)
tcpdump -ni eth0 udp port 4789
```

A successful host-to-host ping should produce VXLAN/UDP traffic on the router underlay. After traffic has passed, `bridge fdb show br br0` should show learned MAC entries.

## 2. Multicast VXLAN

Reset/restart the nodes before switching variants, then run the scripts from `multicast/`. Both VTEPs join multicast group `239.1.1.1`; there is no per-peer `remote` address.

Verify:

```sh
# host 1
ping 192.168.10.2

# routers
ip -d link show vxlan10
ip maddr show dev eth0
bridge fdb show br br0

tcpdump -ni eth0 'udp port 4789 or igmp'
```

`ip -d link show vxlan10` should show `id 10` and `group 239.1.1.1`. The multicast group can be changed, but both routers must use the same group and the underlay must carry multicast between them.

## GNS3 / Docker notes

The router container needs Linux networking privileges required to create bridges and VXLAN interfaces (typically `NET_ADMIN`; GNS3 Docker templates are often run with the needed privileges). The P1 router image must also contain the `ip` and `bridge` commands (`iproute2`) and preferably `tcpdump` for verification.

The P1 requirement that base images have no default IP addresses is preserved: all topology-specific addresses are applied at runtime by these P2 scripts.

## Submission checklist

- Keep the `dogadinm` node naming consistent with P1 (or replace it consistently with another group member's login).
- Keep the commented P2 configuration scripts in the repository.
- Demonstrate both static and multicast VXLAN modes, VNI 10, `br0`, host-to-host connectivity, multicast membership, and the MAC/FDB tables.
- Export the completed GNS3 project using **File → Export portable project**, with the base images included.
- Put the exported ZIP/project in this `P2/` directory (the subject's example calls it `P2.gns3project`).

## Useful defense commands

```sh
ip addr
ip -d link show vxlan10
bridge link
bridge fdb show br br0
ip maddr
ping <other-host-ip>
tcpdump -ni eth0 udp port 4789
```

Be ready to explain: VXLAN, VNI, VTEP, underlay vs overlay, bridge/FDB, MAC learning, static remote VTEP, multicast group, and why VXLAN lets the two hosts behave as if they share one Ethernet segment.
