# BADASS

- [P1 — Docker images and GNS3 setup](P1/README.md): shared `badass-host:p1` and `badass-router:p1` images.
- [P2 — Static and multicast VXLAN](P2/README.md): runtime network configuration using those P1 images.
- [P3](P3/README.md).

Build the shared images and test P1 + P2 from the repository root:

```sh
sh P1/scripts/build.sh
sh P2/scripts/check.sh
```

To use the bundled images without building, replace the build command with
`python3 P1/scripts/load-images.py`. Docker must be running. Tests default to
`linux/amd64`; set `PLATFORM=linux/arm64` for both build and check when using
native ARM images. P2 checks run an isolated Linux namespace topology inside
a disposable privileged Docker container, including on Docker Desktop.
