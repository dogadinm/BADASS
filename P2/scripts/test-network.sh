#!/bin/sh
# Internal test: run through check.sh, never directly on the host.
set -eu
capture_pid=
cleanup() {
    if [ -n "$capture_pid" ]; then
        kill -INT "$capture_pid" 2>/dev/null || :
        wait "$capture_pid" 2>/dev/null || :
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

for node in r1 r2 h1 h2; do
    ip netns add "$node"
    ip -n "$node" link set lo up
done
ip link add underlay type bridge
ip link set underlay up
for i in 1 2; do
    ip link add "sw$i" type veth peer name eth0 netns "r$i"
    ip link set "sw$i" master underlay
    ip link set "sw$i" up
    ip -n "r$i" link add eth1 type veth peer name eth0 netns "h$i"
done

# Repeat scripts, switch to multicast, then switch back to static.
for mode in static multicast static; do
    for pass in 1 2; do
        printf '\nChecking %s, run %s...\n' "$mode" "$pass"
        for i in 1 2; do
            ip netns exec "r$i" sh "/p2/$mode/router$i.sh"
            ip netns exec "h$i" sh "/p2/$mode/host$i.sh"
            details=$(ip -n "r$i" -d link show vxlan10)
            printf '%s\n' "$details" | grep -q 'vxlan id 10 '
            printf '%s\n' "$details" | grep -q 'dstport 4789'
            for port in eth1 vxlan10; do
                ip -n "r$i" link show "$port" | grep -q 'master br0'
                ip -n "r$i" link show "$port" | grep -q 'mtu 1450'
            done
            if [ "$mode" = multicast ]; then
                printf '%s\n' "$details" | grep -q 'group 239.1.1.1'
                ip -n "r$i" maddr show dev eth0 | grep -q '239.1.1.1'
            else
                printf '%s\n' "$details" | grep -q "remote 10.0.0.$((3 - i))"
            fi
        done
        ip netns exec r1 ping -c 2 -W 2 10.0.0.2
        ip netns exec r1 tcpdump -U -ni eth0 -w /tmp/vxlan.pcap \
            'udp port 4789' >/tmp/capture.log 2>&1 &
        capture_pid=$!
        sleep 1
        kill -0 "$capture_pid"
        for i in 1 2; do
            peer=$((3 - i))
            ip netns exec "h$i" ping -c 3 -W 2 "192.168.10.$peer"
            # Maximum non-fragmented IPv4 packet at the configured overlay MTU.
            ip netns exec "h$i" ping -c 2 -W 2 -M do -s 1422 "192.168.10.$peer"
            peer_mac=$(ip netns exec "h$peer" cat /sys/class/net/eth0/address)
            ip netns exec "r$i" bridge fdb show br br0 | grep "$peer_mac dev vxlan10"
        done
        kill -INT "$capture_pid"
        wait "$capture_pid"
        capture_pid=
        tcpdump -nn -r /tmp/vxlan.pcap >/tmp/packets.txt 2>/dev/null
        grep -q 'VXLAN.*vni 10' /tmp/packets.txt
        if [ "$mode" = multicast ]; then
            grep -q '> 239.1.1.1.4789: VXLAN' /tmp/packets.txt
        fi
        # Removing the tunnel must break connectivity: no accidental bypass.
        ip -n r1 link set vxlan10 down
        if ip netns exec h1 ping -c 1 -W 1 192.168.10.2; then
            printf 'FAIL: overlay traffic bypassed VXLAN\n' >&2
            exit 1
        fi
        ip -n r1 link set vxlan10 up
        printf 'PASS: %s run %s (ping, MTU, FDB, capture, isolation)\n' "$mode" "$pass"
    done
done
printf '\nPASS: P2 static and multicast VXLAN using the P1 router image.\n'
