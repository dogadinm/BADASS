#!/usr/bin/env python3
"""Load the bundled Docker images on the same Linux VM as GNS3 Server."""
import argparse
from pathlib import Path
import shutil
import subprocess
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("archive", nargs="?", type=Path, default=Path(__file__).resolve().parents[1] / "P1.gns3project")
args = parser.parse_args()
with zipfile.ZipFile(args.archive) as archive:
    with archive.open("docker-images/images.tar") as source:
        with subprocess.Popen(["docker", "image", "load"], stdin=subprocess.PIPE) as process:
            try:
                shutil.copyfileobj(source, process.stdin)
            finally:
                process.stdin.close()
            if process.wait() != 0:
                raise SystemExit("docker image load failed")
print("Images loaded. Import P1.gns3project in GNS3 on this VM.")
