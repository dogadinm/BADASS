# The same Linux distribution as the host; build for linux/amd64 for school.
FROM alpine:3.23

# FRR includes zebra, BGP, OSPF and IS-IS. tini forwards stop signals and reaps children.
RUN apk add --no-cache frr iproute2 iputils tcpdump tini bash

COPY daemons frr.conf vtysh.conf /etc/frr/
COPY entrypoint.sh /usr/local/bin/router-start
COPY check.sh /usr/local/bin/router-check
RUN chmod 755 /usr/local/bin/router-start /usr/local/bin/router-check \
    && chown -R frr:frr /etc/frr \
    && chmod 640 /etc/frr/frr.conf /etc/frr/vtysh.conf

# GNS3 keeps this directory when a node is stopped and started.
VOLUME ["/etc/frr"]

# No IP addresses or lab-specific interface configuration belong in this image.
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 CMD /usr/local/bin/router-check

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/router-start"]
