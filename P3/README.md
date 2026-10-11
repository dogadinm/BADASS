# P3: OSPF, BGP EVPN and VXLAN

The topology follows the subject's controller-and-leaves diagram. `router_mdogadin-1` is the route reflector (RR). Routers 2, 3 and 4 are VTEP leaves, each attached to one host. All node names contain the 42 login `mdogadin`.

```text
                       router_mdogadin-1 (RR)
                      /          |          \
      router_mdogadin-2  router_mdogadin-3  router_mdogadin-4
              |                  |                  |
      host_mdogadin-1    host_mdogadin-2    host_mdogadin-3
```

| Node | Loopback | Underlay | Overlay host |
| --- | --- | --- | --- |
| RR | `1.1.1.1/32` | `10.1.1.1/30`, `10.1.1.5/30`, `10.1.1.9/30` | none |
| Leaf 2 | `1.1.1.2/32` | `10.1.1.2/30` | `192.168.10.1/24` |
| Leaf 3 | `1.1.1.3/32` | `10.1.1.6/30` | `192.168.10.2/24` |
| Leaf 4 | `1.1.1.4/32` | `10.1.1.10/30` | `192.168.10.3/24` |

`router*/network.sh` creates the interfaces, bridge `br0` and VXLAN VNI 10. `router*/frr.conf` configures OSPF area 0 for the underlay and iBGP EVPN in AS 65000. The RR reflects EVPN routes between leaves. Type 3 announces participation in the VNI; type 2 announces a learned host MAC. The RR forwards underlay IP traffic but does not terminate VXLAN.

The `hosts/host*.sh` scripts deliberately start with **no IPv4 address**, as required for the MAC-only learning demonstration. Assign IPs manually only for the final ping stage. All network scripts run automatically when a node starts.

## Demonstration order

Import `P3/P3.gns3project`. Open **Auxiliary console** and run `exec /bin/sh` before the commands below.

1. Start only the four routers. On the RR run:

   ```sh
   vtysh -c 'show ip ospf neighbor'
   vtysh -c 'show bgp l2vpn evpn summary'
   vtysh -c 'show bgp l2vpn evpn route'
   ```

   Expect three OSPF neighbors, three EVPN peers, type-3 routes and no host type-2 routes. On leaf 4, `vtysh -c 'show ip route ospf'` shows paths to the other loopbacks.

2. Start only `host_mdogadin-1`. On the host, verify that `ip -4 addr show dev eth0` lists no address, then send an ARP probe without assigning one:

   ```sh
   arping -D -I eth0 -c 3 192.168.10.254
   cat /sys/class/net/eth0/address
   ```

   Compare that MAC with `vtysh -c 'show bgp l2vpn evpn route'` on leaf 2 and leaf 4. A type-2 route appears after the leaf receives a frame from the host. Starting a silent host alone may not create a route.

3. Start hosts 2 and 3. Their MACs can be demonstrated with the same ARP probe. Then assign overlay addresses, one command in each host console:

   ```sh
   # host 1
   ip addr replace 192.168.10.1/24 dev eth0
   # host 2
   ip addr replace 192.168.10.2/24 dev eth0
   # host 3
   ip addr replace 192.168.10.3/24 dev eth0
   ```

   From host 1, ping `192.168.10.2` and `192.168.10.3`. Capture the RR-to-leaf link in Wireshark. Filter for `vxlan` to inspect UDP port 4789 and VNI 10, and `ospf` to show OSPF packets. After stopping and restarting hosts, repeat the IP assignments for the ping stage.

The IP addresses shown in the subject are illustrative; this project keeps the required topology, protocols, VNI 10 and no-IP learning stage.
