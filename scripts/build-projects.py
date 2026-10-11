#!/usr/bin/env python3
"""Rebuild portable P2/P3 projects from versioned configs and P1's amd64 images."""
import copy
import json
from pathlib import Path
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = uuid.UUID("80172bcc-e93e-44b3-9c82-d11977bb1df3")


def uid(name):
    return str(uuid.uuid5(NAMESPACE, name))


def build(name, part, mode=None):
    project = json.loads((ROOT / "P1/P1.gns3").read_text())
    templates = {n["name"].split("_")[0]: n for n in project["topology"]["nodes"]}
    project.update(name=name, project_id=uid(name))
    project["topology"] = {"computes": [], "drawings": [], "links": [], "nodes": []}
    files = {}
    nodes = {}

    def node(kind, number, x, y):
        key = f"{kind}{number}"
        obj = copy.deepcopy(templates[kind])
        obj.update(node_id=uid(name + key), name=f"{kind}_mdogadin-{number}", x=x, y=y)
        obj["label"]["text"] = obj["name"]
        obj["console"] = None
        props = obj["properties"]
        props.update(aux=None, container_id=None, mac_address=None,
                     start_command="/bin/sh /etc/network/start.sh")
        nodes[key] = obj
        project["topology"]["nodes"].append(obj)
        base = f"project-files/docker/{obj['node_id']}"
        if part == 2:
            network = (ROOT / f"P2/{mode}/{key}.sh").read_text()
        else:
            path = f"P3/router{number}/network.sh" if kind == "router" else f"P3/hosts/host{number}.sh"
            network = (ROOT / path).read_text()
        files[f"{base}/etc/network/lab.sh"] = network
        files[f"{base}/etc/network/interfaces"] = "# Addresses are applied by /etc/network/start.sh.\n"
        files[f"{base}/etc/network/.gns3_perms"] = ""
        # /etc/network and /etc/frr are persistent GNS3 volumes.
        files[f"{base}/etc/network/start.sh"] = (
            "#!/bin/sh\nset -eu\n/sbin/ip link set lo up\n"
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\nexport PATH\n"
            "sh /etc/network/lab.sh\n" +
            ("exec /usr/local/bin/router-start\n" if kind == "router" else "exec /bin/sh\n")
        )
        if kind == "router":
            # This marker tells GNS3 that the volume is already populated.
            # Without it, init.sh overwrites frr.conf with the P1 image default.
            # UID/GID match FRR in the bundled P1 Alpine image.
            files[f"{base}/etc/frr/.gns3_perms"] = (
                "755:100:101:/etc/frr\n"
                "644:100:101:/etc/frr/daemons\n"
                "640:100:101:/etc/frr/frr.conf\n"
                "640:100:101:/etc/frr/vtysh.conf\n"
            )
            for filename in ["frr.conf", "daemons", "vtysh.conf"]:
                source = ROOT / "P1/router" / filename
                if part == 3 and filename == "frr.conf":
                    source = ROOT / f"P3/router{number}/frr.conf"
                files[f"{base}/etc/frr/{filename}"] = source.read_text()
        return obj

    def link(a, pa, b, pb):
        project["topology"]["links"].append({
            "link_id": uid(f"{name}/{a}/{pa}/{b}/{pb}"),
            "nodes": [{"node_id": nodes[key]["node_id"], "adapter_number": port, "port_number": 0}
                      for key, port in [(a, pa), (b, pb)]],
        })

    if part == 2:
        for i, x in [(1, -220), (2, 220)]:
            node("router", i, x, 0)
            node("host", i, x, 200)
            link(f"router{i}", 1, f"host{i}", 0)
        switch = {
            "node_id": uid(name + "switch"), "name": "switch_mdogadin-1",
            "node_type": "ethernet_switch", "compute_id": "local", "x": 0, "y": -170,
            "symbol": ":/symbols/ethernet_switch.svg", "label": {"text": "switch_mdogadin-1", "x": 0, "y": -30},
            "properties": {"ports_mapping": [{"name": f"Ethernet{i}", "port_number": i, "type": "access", "vlan": 1} for i in range(2)]},
        }
        project["topology"]["nodes"].append(switch)
        for i in (1, 2):
            project["topology"]["links"].append({
                "link_id": uid(name + f"switch-link-{i}"), "nodes": [
                    {"node_id": switch["node_id"], "adapter_number": 0, "port_number": i - 1},
                    {"node_id": nodes[f"router{i}"]["node_id"], "adapter_number": 0, "port_number": 0}],
            })
    else:
        node("router", 1, 0, -210)
        for i, x in [(2, -300), (3, 0), (4, 300)]:
            node("router", i, x, 0)
            node("host", i - 1, x, 200)
            link("router1", i - 2, f"router{i}", 0)
            link(f"router{i}", 1, f"host{i-1}", 0)

    folder = ROOT / f"P{part}"
    payload = json.dumps(project, indent=4) + "\n"
    (folder / f"{name}.gns3").write_text(payload)
    with zipfile.ZipFile(ROOT / "P1/P1.gns3project") as source:
        with zipfile.ZipFile(folder / f"{name}.gns3project", "w", zipfile.ZIP_DEFLATED) as out:
            out.writestr("project.gns3", payload)
            for path, contents in sorted(files.items()):
                out.writestr(path, contents)
            for path in ["docker-images/images.tar", "docker-images/manifest.json"]:
                out.writestr(path, source.read(path))
            out.writestr("docker-images/IMPORT.txt", f"Load images before importing: python3 P1/scripts/load-images.py P{part}/{name}.gns3project\n")
    print(f"Built P{part}/{name}.gns3project")


if __name__ == "__main__":
    build("P2", 2, "static")
    build("P2-multicast", 2, "multicast")
    build("P3", 3)
