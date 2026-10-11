# BADASS

GNS3 projects for the three mandatory parts of the BADASS subject. All equipment names contain the 42 login `mdogadin`. The shared Docker images target `linux/amd64` and have no preset IP addresses.

| Part | Project | Configuration |
| --- | --- | --- |
| P1: Docker and FRRouting | `P1/P1.gns3project` | `P1/host/`, `P1/router/` |
| P2: static VXLAN | `P2/P2.gns3project` | `P2/static/` |
| P2: multicast VXLAN | `P2/P2-multicast.gns3project` | `P2/multicast/` |
| P3: OSPF, BGP EVPN and VXLAN | `P3/P3.gns3project` | `P3/hosts/`, `P3/router*/` |

The [P1](P1/README.md), [P2](P2/README.md), and [P3](P3/README.md) READMEs describe the configurations and how to reproduce the subject's demonstrations. The `.gns3project` files are the complete portable exports; the `.gns3` files are readable topology sources.

On the Linux VM running GNS3 Server:

```sh
python3 P1/scripts/load-images.py
sh P2/scripts/check.sh
```

Import each `.gns3project` through **File > Import portable project**. The GNS3 Docker images are bundled in the exports but must be loaded into Docker once with the command above.

After editing source configurations, rebuild the P2/P3 exports and verify them:

```sh
python3 scripts/build-projects.py
python3 scripts/check-gns3.py
```

The root `scripts/` directory contains optional maintenance tools: `build-projects.py` regenerates P2/P3 portable exports from their configuration files, and `check-gns3.py` checks temporary imported projects against a running local GNS3 Server. Neither script is needed to run the supplied exports. All network configuration files are inside P1, P2, and P3.
