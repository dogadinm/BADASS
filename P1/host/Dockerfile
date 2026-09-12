# Lightweight Linux with BusyBox included.
FROM alpine:3.23

# Tools for configuring interfaces and diagnosing network traffic.
RUN apk add --no-cache \
    iproute2 \
    iputils \
    tcpdump

# Start a shell for the host console.
CMD ["/bin/sh"]