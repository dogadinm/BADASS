#!/usr/bin/env python3
"""Add Docker base images to a real GNS3 portable export (GNS3 skips them)."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="Portable project exported by GNS3")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "P1.gns3project")
    args = parser.parse_args()
    with zipfile.ZipFile(args.export) as source:
        project = json.loads(source.read("project.gns3"))
        tags = sorted({node["properties"]["image"] for node in project["topology"]["nodes"] if node["node_type"] == "docker"})
        if tags != ["badass-host:p1", "badass-router:p1"]:
            parser.error("Expected exactly badass-host:p1 and badass-router:p1 in P1")
        metadata = json.loads(subprocess.check_output(["docker", "image", "inspect", *tags]))
        if any(image["Architecture"] != "amd64" or image["Os"] != "linux" for image in metadata):
            parser.error("Build both images for linux/amd64 before packaging for school")
        with tempfile.TemporaryDirectory(prefix="badass-p1-package-") as temporary:
            images = Path(temporary) / "images.tar"
            subprocess.run(["docker", "image", "save", "-o", str(images), *tags], check=True)
            packed = Path(temporary) / "P1.gns3project"
            with zipfile.ZipFile(packed, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as target:
                for item in source.infolist():
                    if not item.filename.startswith("docker-images/"):
                        target.writestr(item, source.read(item.filename))
                target.write(images, "docker-images/images.tar")
                manifest = [{"tags": i["RepoTags"], "id": i["Id"], "os": i["Os"], "architecture": i["Architecture"]} for i in metadata]
                target.writestr("docker-images/manifest.json", json.dumps(manifest, indent=2) + "\n")
                target.writestr("docker-images/IMPORT.txt", "On the Linux VM running GNS3 Server, load the images BEFORE importing this project:\nunzip -p P1.gns3project docker-images/images.tar | docker load\nThen import P1.gns3project in GNS3.\n")
            with zipfile.ZipFile(packed) as check:
                if check.testzip() is not None:
                    raise RuntimeError("Archive integrity check failed")
            # Source and output may be the same path: the source is fully read already.
            args.output.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copyfile(packed, args.output)
    print(f"Created {args.output} ({args.output.stat().st_size / 1024 / 1024:.1f} MiB), including both Docker images")


if __name__ == "__main__":
    main()
