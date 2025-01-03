ARG VERSION
FROM openeuler/openeuler:${VERSION} AS builder

ARG TARGETARCH
ARG BUILDARCH
ARG PACKAGES
ARG VERSION
ARG BUILD_ROOT=/var/tmp/containers/distroless/openEuler-docker-rootfs/

COPY build.py /tmp/

RUN set -eux; \
    if [ "$TARGETARCH" = "amd64" ]; then \
      BUILDARCH="x86_64"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
      BUILDARCH="aarch64"; \
    fi; \
    yum -y install wget xz python3-pip; \
    pip3 install click; \
    python3 /tmp/build.py -p ${BUILD_ROOT} -a ${BUILDARCH} -l ${PACKAGES} -v ${VERSION}

FROM scratch
ARG BUILD_ROOT=/var/tmp/containers/distroless/openEuler-docker-rootfs/
COPY --from=builder ${BUILD_ROOT} /
COPY --from=builder /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
COPY --from=builder /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt

CMD ["bash"]
