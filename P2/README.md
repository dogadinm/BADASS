# P2: static and multicast VXLAN

Both exports use the same topology as the subject: two hosts connected to two routers, with an Ethernet switch joining the routers' underlay interfaces. Equipment names contain `mdogadin`.

`P2.gns3` and `P2-multicast.gns3` contain the same topology. They are JSON topology sources, not older project versions. Import the matching `.gns3project` archive: it also contains the Docker images and the mode-specific startup configuration.

```text
host_mdogadin-1 -- router_mdogadin-1 -- switch_mdogadin-1 -- router_mdogadin-2 -- host_mdogadin-2
```

| Network | Addresses or setting |
| --- | --- |
| Underlay, router `eth0` | `10.0.0.1/24`, `10.0.0.2/24` |
| Overlay, host `eth0` | `192.168.10.1/24`, `192.168.10.2/24` |
| Router bridge | `br0`: access `eth1` + `vxlan10` |
| VXLAN | VNI `10`, UDP port `4789` |
| Overlay MTU | `1450` over a 1500-byte IPv4 underlay |

`P2/P2.gns3project` uses an explicit `remote` VTEP address in `static/router*.sh`. `P2/P2-multicast.gns3project` uses group `239.1.1.1` in `multicast/router*.sh`, so a peer address is not configured on each VTEP. The host and router scripts are commented and applied automatically at node start from persistent `/etc/network/lab.sh`.

Import and start each project separately. In each **Auxiliary console**, first run `exec /bin/sh`. On host 1:

```sh
ping -c 3 192.168.10.2
```

On either router:

```sh
ip -d link show vxlan10
bridge link
bridge fdb show br br0
```

The VXLAN output must show `id 10`. It shows `remote 10.0.0.x` in the static project and `group 239.1.1.1` in the multicast project. The bridge must contain `eth1` and `vxlan10`; after traffic, its FDB contains the remote host MAC.

To reproduce the subject's Wireshark view, right-click the router-to-switch link in GNS3 and select **Start capture**. Then ping from host 1. Filter for `vxlan` or `icmp` in Wireshark and expand the packet: outer IP, UDP destination port 4789, VXLAN VNI 10, inner Ethernet/IP/ICMP. The IP addresses in the subject's screenshots are examples; the mandatory values are VNI 10 and bridge `br0`.
