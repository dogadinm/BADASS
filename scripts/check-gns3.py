#!/usr/bin/env python3
"""Import disposable projects into GNS3 2.2, test via auxiliary consoles, delete them.

Run on the Linux machine hosting GNS3 Server. Uses only Python's standard library.
Only random project UUIDs created by this invocation are stopped/deleted.
"""
import argparse
import io
import json
import os
import base64
from pathlib import Path
import re
import shlex
import socket
import time
import urllib.request
import urllib.error
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class Console:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port), timeout=10)
        self.sock.settimeout(1)
        self.pending = b""
        self.sock.sendall(b"\r\nexec /bin/sh\r\n")
        time.sleep(0.3)

    def read(self):
        try:
            data = self.pending + self.sock.recv(65536)
        except socket.timeout:
            return b""
        self.pending = b""
        result = bytearray()
        i = 0
        while i < len(data):
            if data[i] != 255:
                result.append(data[i]); i += 1
                continue
            if i + 1 >= len(data):
                self.pending = data[i:]; break
            cmd = data[i+1]
            if cmd == 255:
                result.append(255); i += 2
            elif cmd in (251, 252, 253, 254):
                if i + 2 >= len(data):
                    self.pending = data[i:]; break
                if cmd in (251, 253):
                    self.sock.sendall(bytes([255, 254 if cmd == 251 else 252, data[i+2]]))
                i += 3
            elif cmd == 250:
                end = data.find(b"\xff\xf0", i + 2)
                if end < 0:
                    self.pending = data[i:]; break
                i = end + 2
            else:
                i += 2
        return bytes(result)

    def run(self, command, timeout=30):
        token = "DONE_" + uuid.uuid4().hex
        begin = "BEGIN_" + token
        wrapped = f"printf '\\n{begin}\\n'; sh -c {shlex.quote(command)}; printf '\\n{token}:%s\\n' \"$?\"\n"
        self.sock.sendall(wrapped.encode())
        output = b""
        deadline = time.monotonic() + timeout
        pattern = re.compile(rb"(?:\r?\n)" + token.encode() + rb":(\d+)\r?\n")
        while time.monotonic() < deadline:
            output += self.read()
            match = pattern.search(output)
            if match:
                text = output[:match.start()].decode(errors="replace").replace("\r", "")
                # A long echoed command can wrap over many terminal lines.
                text = text.split("\n" + begin + "\n", 1)[-1]
                if int(match[1]):
                    raise RuntimeError(f"Command failed: {command}\n{text}")
                return text
        raise TimeoutError(f"Console timeout: {command}\n{output.decode(errors='replace')}")

    def close(self):
        self.sock.close()


def retry(action, seconds=90):
    deadline = time.monotonic() + seconds
    while True:
        try:
            return action()
        except (RuntimeError, AssertionError) as exc:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Did not converge: {exc}") from exc
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:3080")
    parser.add_argument("--console-host", default="127.0.0.1")
    parser.add_argument("--user", help="GNS3 HTTP user; password is read from GNS3_PASSWORD")
    parser.add_argument("--projects", nargs="+", choices=["P2", "P2-multicast", "P3"], default=["P2", "P2-multicast", "P3"])
    parser.add_argument("--export-dir", type=Path, help="Save GNS3 exports with bundled images after successful tests")
    args = parser.parse_args()

    def api(method, path, data=None, raw=False):
        headers = {"Content-Type": "application/octet-stream" if isinstance(data, bytes) else "application/json"}
        if args.user:
            credentials = f"{args.user}:{os.environ.get('GNS3_PASSWORD', '')}"
            headers["Authorization"] = "Basic " + base64.b64encode(credentials.encode()).decode()
        if data is not None and not isinstance(data, bytes):
            data = json.dumps(data).encode()
        request = urllib.request.Request(args.url.rstrip("/") + "/v2" + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = response.read()
                return body if raw else (json.loads(body) if body else None)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"GNS3 {method} {path}: {exc.code} {exc.read().decode(errors='replace')}") from exc

    print("GNS3", api("GET", "/version"), flush=True)
    for name in args.projects:
        source = ROOT / ("P3" if name == "P3" else "P2") / f"{name}.gns3project"
        project_id = str(uuid.uuid4())
        base = f"/projects/{project_id}"
        consoles = {}
        created = False
        try:
            print(f"Import {name} as disposable project {project_id}", flush=True)
            api("POST", base + "/import", source.read_bytes())
            created = True
            api("POST", base + "/open")
            nodes = api("GET", base + "/nodes")
            by_name = {n["name"]: n for n in nodes}

            def start(node):
                api("POST", base + f"/nodes/{node['node_id']}/start")

            def connect():
                for c in consoles.values(): c.close()
                consoles.clear()
                for n in api("GET", base + "/nodes"):
                    if n["node_type"] == "docker" and n["status"] == "started":
                        consoles[n["name"]] = Console(args.console_host, n["properties"]["aux"])

            def run(key, command):
                return consoles[key].run(command)

            def router(i, command):
                return run(f"router_mdogadin-{i}", command)

            def host(i, command):
                return run(f"host_mdogadin-{i}", command)

            def ready():
                for key in consoles:
                    if key.startswith("router_"): run(key, "/usr/local/bin/router-check")

            if name == "P3":
                for n in nodes:
                    if n["name"].startswith("router_"): start(n)
                connect()
                retry(ready)

                def control_plane():
                    rr_summary = json.loads(router(1, "vtysh -c 'show bgp l2vpn evpn summary json'"))
                    assert rr_summary.get("dynamicPeers") == 3, rr_summary
                    assert all(peer.get("state") == "Established" for peer in rr_summary["peers"].values()), rr_summary
                    for i in (2, 3, 4):
                        summary = json.loads(router(i, "vtysh -c 'show bgp l2vpn evpn summary json'"))
                        assert summary.get("peers", {}).get("1.1.1.1", {}).get("state") == "Established", summary
                        router(i, "vtysh -c 'show ip ospf neighbor' | grep -q Full")
                        for peer in (2, 3, 4):
                            if peer != i: router(i, f"ping -c 1 -W 2 1.1.1.{peer} >/dev/null")
                        table = router(i, "vtysh -c 'show bgp l2vpn evpn route'")
                        assert table.count("[3]:[0]:[32]:") >= 3, table
                retry(control_plane)
                for i in (2, 3, 4):
                    table = router(i, "vtysh -c 'show bgp l2vpn evpn route'")
                    assert "[2]:[0]:" not in table, table
                print("PASS: OSPF, dynamic RR clients, EVPN type 3 before hosts; no type 2", flush=True)
                # Start one host at a time. The P3 host startup scripts assign no IP.
                macs = []
                for i in (1, 2, 3):
                    start(by_name[f"host_mdogadin-{i}"])
                    connect()
                    host(i, "test -z \"$(ip -o -4 addr show dev eth0)\"")
                    host(i, "arping -D -I eth0 -c 2 192.168.10.254 >/dev/null")
                    mac = host(i, "cat /sys/class/net/eth0/address").strip().splitlines()[-1]
                    macs.append(mac)

                    def mac_routes():
                        for router_number in (1, 2, 3, 4):
                            table = router(router_number, "vtysh -c 'show bgp l2vpn evpn route'")
                            for learned_mac in macs: assert learned_mac in table, table
                    retry(mac_routes)
                print("PASS: MAC-only type 2 routes propagated by RR without host IPs", flush=True)
                for i in (1, 2, 3): host(i, f"ip addr replace 192.168.10.{i}/24 dev eth0")
            else:
                for n in nodes: start(n)
                connect()
                retry(ready)

            def connectivity():
                count = 3 if name == "P3" else 2
                for i in range(1, count+1):
                    for peer in range(1, count+1):
                        if i != peer:
                            host(i, f"ping -c 2 -W 2 -M do -s 1422 192.168.10.{peer} >/dev/null")
                host_macs = {i: host(i, "cat /sys/class/net/eth0/address").strip() for i in range(1, count+1)}
                for i in ((2, 3, 4) if name == "P3" else (1, 2)):
                    router(i, "ip -d link show vxlan10 | grep -q 'vxlan id 10 '")
                    router(i, "bridge link show | grep -q 'master br0'")
                    if name == "P3":
                        router(i, "bridge fdb show dev vxlan10 | grep -q extern_learn")
                    elif name == "P2-multicast":
                        router(i, "ip maddr show dev eth0 | grep -q 239.1.1.1")
                    local_host = i - 1 if name == "P3" else i
                    fdb = router(i, "bridge fdb show dev vxlan10")
                    for peer, mac in host_macs.items():
                        if peer != local_host: assert mac in fdb, fdb
            retry(connectivity)
            print(f"PASS: {name} all-pairs ping, 1450-byte MTU and FDB", flush=True)
            leaf = 2 if name == "P3" else 1
            router(leaf, "tcpdump -U -ni eth0 -w /tmp/check-vxlan.pcap 'udp port 4789' >/tmp/check-capture.log 2>&1 & echo $! >/tmp/check-capture.pid")
            time.sleep(1)
            host(1, "ip neigh flush dev eth0; ping -c 2 -W 2 192.168.10.2 >/dev/null")
            router(leaf, "kill -INT $(cat /tmp/check-capture.pid)")
            time.sleep(1)
            packets = router(leaf, "tcpdump -nn -r /tmp/check-vxlan.pcap 2>/dev/null")
            assert "vni 10" in packets, packets
            if name == "P2-multicast": assert "239.1.1.1.4789" in packets, packets
            print("PASS: packet capture confirms VXLAN VNI 10", flush=True)
            router(leaf, "ip link set vxlan10 down")
            host(1, "if ping -c 1 -W 2 192.168.10.2 >/dev/null; then exit 1; fi")
            router(leaf, "ip link set vxlan10 up")
            retry(connectivity)
            print("PASS: traffic fails with tunnel down and recovers", flush=True)

            for c in consoles.values(): c.close()
            consoles.clear()
            api("POST", base + "/nodes/stop")
            api("POST", base + "/nodes/start")
            connect()
            retry(ready)
            if name == "P3":
                for i in (1, 2, 3): host(i, f"ip addr replace 192.168.10.{i}/24 dev eth0")
            retry(connectivity)
            print(f"PASS: {name} stop/start restores configuration automatically", flush=True)
            for c in consoles.values(): c.close()
            consoles.clear()
            api("POST", base + "/nodes/stop")
            if args.export_dir:
                exported = api("GET", base + "/export?include_images=true", raw=True)
                args.export_dir.mkdir(parents=True, exist_ok=True)
                path = args.export_dir / f"{name}.gns3project"
                with zipfile.ZipFile(io.BytesIO(exported)) as inp, zipfile.ZipFile(source) as original:
                    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
                        for item in inp.infolist():
                            if not item.filename.startswith("docker-images/"):
                                out.writestr(item, inp.read(item.filename))
                        for item in original.infolist():
                            if item.filename.startswith("docker-images/"): out.writestr(item, original.read(item.filename))
                print("Exported", path, flush=True)
        except Exception:
            for key, console in consoles.items():
                if key.startswith("router_"):
                    try:
                        print(key, console.run("ip -br addr; ip route; vtysh -c 'show running-config' -c 'show ip ospf neighbor' -c 'show bgp l2vpn evpn summary'"), flush=True)
                    except Exception as diagnostic_error:
                        print("Diagnostic failed:", diagnostic_error, flush=True)
            raise
        finally:
            for c in consoles.values(): c.close()
            if created: api("DELETE", base)
    print("PASS: all requested GNS3 integration checks", flush=True)


if __name__ == "__main__":
    main()
