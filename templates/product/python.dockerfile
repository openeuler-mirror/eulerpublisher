# Arguments
ARG PY_VERSION={{ version }}

# Stage 1: Install Python
FROM openeuler/openeuler:{{ dependence }} AS py-installer

ARG PY_VERSION
ENV PATH=/usr/local/python${PY_VERSION}/bin:${PATH}

# Install dependencies
RUN yum update -y && \
    yum install -y \
        gcc \
        gcc-c++ \
        make \
        cmake \
        curl \
        zlib-devel \
        bzip2-devel \
        openssl-devel \
        ncurses-devel \
        sqlite-devel \
        readline-devel \
        tk-devel \
        gdbm-devel \
        libpcap-devel \
        xz-devel \
        libev-devel \
        expat-devel \
        libffi-devel \
        systemtap-sdt-devel \
    && yum clean all \
    && rm -rf /var/cache/yum \
    && rm -rf /tmp/*

RUN PY_HOME=/usr/local/python${PY_VERSION} && \
    PY_INSTALLER_TGZ=Python-${PY_VERSION}.tgz && \
    PY_INSTALLER_DIR=Python-${PY_VERSION} && \
    PY_INSTALLER_URL=https://repo.huaweicloud.com/python/${PY_VERSION}/${PY_INSTALLER_TGZ} && \
    curl -fsSL -o "/tmp/${PY_INSTALLER_TGZ}" "${PY_INSTALLER_URL}" && \
    tar -xf /tmp/${PY_INSTALLER_TGZ} -C /tmp && \
    cd /tmp/${PY_INSTALLER_DIR} && \
    mkdir -p ${PY_HOME}/lib && \
    ./configure --prefix=${PY_HOME} --enable-shared LDFLAGS="-Wl,-rpath ${PY_HOME}/lib" && \
    make -j "$(nproc)" && \
    make altinstall && \
    ln -sf ${PY_HOME}/bin/python${PY_VERSION} ${PY_HOME}/bin/python3 && \
    ln -sf ${PY_HOME}/bin/pip3 ${PY_HOME}/bin/pip3 && \
    ln -sf ${PY_HOME}/bin/python3 ${PY_HOME}/bin/python && \
    ln -sf ${PY_HOME}/bin/pip3 ${PY_HOME}/bin/pip && \
    rm -rf /tmp/${PY_INSTALLER_TGZ} /tmp/${PY_INSTALLER_DIR} && \
    ${PY_HOME}/bin/python -c "import sys; print(sys.version)"

# Stage 2: Copy results from previous stages
FROM openeuler/openeuler:{{ dependence }} AS official

ARG PY_VERSION
ENV PATH=/usr/local/python${PY_VERSION}/bin:${PATH}

# Change the default shell
SHELL [ "/bin/bash", "-c" ]

# Install dependencies
RUN yum update -y && \
    yum install -y \
        ca-certificates \
        bash \
        glibc \
        sqlite-devel \
    && yum clean all \
    && rm -rf /var/cache/yum \
    && rm -rf /tmp/*

# Copy files
COPY --from=py-installer /usr/local/python${PY_VERSION} /usr/local/python${PY_VERSION}

# Set environment variables
RUN \
    # Set environment variables for Python \
    PY_PATH="PATH=/usr/local/python${PY_VERSION}/bin:\${PATH}" && \
    echo "export ${PY_PATH}" >> /etc/profile && \
    echo "export ${PY_PATH}" >> ~/.bashrc