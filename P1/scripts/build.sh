#!/bin/sh
set -eu
p1_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
platform=${PLATFORM:-linux/amd64}
docker build --platform "$platform" -t badass-host:p1 "$p1_dir/host"
docker build --platform "$platform" -t badass-router:p1 "$p1_dir/router"
