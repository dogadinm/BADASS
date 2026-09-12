#!/bin/sh
set -eu
platform=${PLATFORM:-linux/amd64}
router="badass-p1-check-$$"
created=no
cleanup() {
    if [ "$created" = yes ]; then docker rm -fv "$router" >/dev/null 2>&1 || :; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf 'Checking host tools and absence of configured IP addresses...\n'
docker run --rm --platform "$platform" --network none badass-host:p1 sh -ec '
    command -v busybox
    command -v ip
    command -v ping
    command -v tcpdump
    ping -c 3 127.0.0.1
    test -z "$(ip -o addr show scope global)"
'

# FRR needs SYS_ADMIN as well as network capabilities for namespace support.
# GNS3 itself supplies the required container privileges.
docker run -d --platform "$platform" --network none \
    --cap-add NET_ADMIN --cap-add NET_RAW --cap-add SYS_ADMIN \
    --ulimit nofile=4096:4096 \
    --name "$router" badass-router:p1 >/dev/null
created=yes

wait_ready() {
    attempt=0
    until docker exec "$router" /usr/local/bin/router-check >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        if [ "$attempt" -ge 60 ]; then
            docker logs "$router"
            printf 'FAIL: routing services did not become ready.\n' >&2
            exit 1
        fi
        sleep 1
    done
}
wait_ready
printf 'Checking effective routing configuration...\n'
config=$(docker exec "$router" vtysh -c 'show running-config')
printf '%s\n' "$config"
printf '%s\n' "$config" | grep -q '^router bgp 65000'
printf '%s\n' "$config" | grep -q '^router ospf'
printf '%s\n' "$config" | grep -q '^router isis P1'

docker exec "$router" sh -ec 'test -z "$(ip -o addr show scope global)"'
docker exec "$router" vtysh -c 'show ip ospf' -c 'show bgp summary' -c 'show isis summary'

printf 'Checking restart and configuration reload...\n'
docker restart "$router" >/dev/null
wait_ready
config=$(docker exec "$router" vtysh -c 'show running-config')
printf '%s\n' "$config" | grep -q '^router bgp 65000'
printf '%s\n' "$config" | grep -q '^router ospf'
printf '%s\n' "$config" | grep -q '^router isis P1'
docker exec "$router" sh -ec 'test -z "$(ip -o addr show scope global)"'
printf 'PASS: host, routing daemons, protocol configuration, no preset IPs, restart.\n'
