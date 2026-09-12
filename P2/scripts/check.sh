#!/bin/sh
# Run from any directory; P2 consumes the images built or loaded by P1.
set -eu
p2_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
platform=${PLATFORM:-linux/amd64}
sh "$p2_dir/../P1/scripts/check.sh"

# Namespaces and the switch exist only inside this disposable container.
# Privileged mode is required for ip netns and VXLAN on Docker's Linux VM.
docker run --rm --platform "$platform" --network none --privileged \
    --entrypoint /bin/sh -v "$p2_dir:/p2:ro" \
    badass-router:p1 /p2/scripts/test-network.sh
