ARG VERSION=24.03-lts
FROM openeuler/openeuler:${VERSION} AS builder

ARG TARGETARCH
ARG BUILDARCH
ARG PACKAGES
ARG BUILD_ROOT=/var/tmp/containers/distroless/openEuler-docker-rootfs

COPY build.py /tmp/

RUN if [ "$TARGETARCH" = "amd64" ]; then \
      BUILDARCH="x86_64"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
      BUILDARCH="aarch64"; \
    fi; \
    yum -y install wget xz python3-pip; \
    pip3 instll click; \
    python3 /tmp/build.py -p ${BUILD_ROOT} -a ${BUILDARCH} -l ${PACKAGES} -v ${VERSION}

FROM scratch

COPY --from=builder /var/tmp/containers/distroless/openEuler-docker-rootfs/ /
COPY --from=builder /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
COPY --from=builder /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt

CMD ["bash"]
