FROM scratch
ARG TARGETARCH
ARG EULER_VERSION={{ version }}

RUN if [ "${TARGETPLATFORM}" = "linux/amd64" ]; then \
        ARCH="x86_64"; \
    else \
        ARCH="aarch64"; \
    fi && \
    EULER_URL=https://repo.openeuler.org/openEuler-${EULER_VERSION}/docker_img/${ARCH}/openEuler-docker.${ARCH}.tar.xz && \
    EULER_TGZ=EULER-${EULER_VERSION}.tgz && \
    curl -fsSL -o "/tmp/${EULER_TGZ}" "${EULER_URL}"

ADD /tmp/${EULER_TGZ} /
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && \
    sed -i "s/TMOUT=300/TMOUT=0/g" /etc/bashrc
CMD ["bash"]


