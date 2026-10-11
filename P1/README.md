# P1: GNS3 and Docker

The project contains two running, unconnected nodes: `host_mdogadin-1` and `router_mdogadin-1`. This follows the subject's P1 diagram. Both are reachable through GNS3 consoles.

- `host/Dockerfile` builds an Alpine host with BusyBox and network tools.
- `router/Dockerfile` builds an Alpine router with FRRouting, BusyBox and network tools.
- `router/daemons` enables `zebra`, `bgpd`, `ospfd` and `isisd`; `router/frr.conf` creates the base protocol instances. The router image has no configured interface IPs.
- `router/entrypoint.sh` starts FRRouting; `router/check.sh` checks its daemons.
- `scripts/build.sh` builds both images for `linux/amd64`; `scripts/load-images.py` loads the images bundled in the export.

From the repository root in the Linux VM:

```sh
python3 P1/scripts/load-images.py
sh P1/scripts/check.sh
```

Import `P1/P1.gns3project`, start both nodes, and open each node's **Auxiliary console**. Run `exec /bin/sh` first. The GNS3 auxiliary shell otherwise uses a limited BusyBox command set.

On the host:

```sh
hostname
command -v busybox
ip -br addr
```

On the router:

```sh
hostname
ps
/usr/local/bin/router-check
vtysh -c 'show running-config'
```

`router-check` is silent on success. No neighbor sessions are expected in P1 because the nodes are unconnected. The images are reused without preset IPs in P2 and P3; those projects apply their own addresses at runtime.
