# Stage 1: Install CANN
FROM ascendai/python:{{ dependence }} AS cann-installer

# Arguments
ARG TARGETPLATFORM
ARG CANN_CHIP=910b
ARG CANN_VERSION={{ version }}
ARG BASE_URL=https://ascend-repo.obs.cn-east-2.myhuaweicloud.com

RUN if [ "${TARGETPLATFORM}" = "linux/amd64" ]; then \
        ARCH="x86_64"; \
    else \
        ARCH="aarch64"; \
    fi && \
    URL_PREFIX="${BASE_URL}/CANN/CANN%20${CANN_VERSION}" && \
    TOOLKIT_FILE="Ascend-cann-toolkit_${CANN_VERSION}_linux-${ARCH}.run" && \
    KERNELS_FILE="Ascend-cann-kernels-${CANN_CHIP}_${CANN_VERSION}_linux-${ARCH}.run" && \
    NNAL_FILE="Ascend-cann-nnal_${CANN_VERSION}_linux-${ARCH}.run" && \
    CANN_TOOLKIT_URL="${URL_PREFIX}/${TOOLKIT_FILE}" && \
    CANN_KERNELS_URL="${URL_PREFIX}/${KERNELS_FILE}" && \
    CANN_NNAL_URL="${URL_PREFIX}/${NNAL_FILE}" && \
    echo "${CANN_TOOLKIT_URL}" > /tmp/toolkit_url_file.txt && \
    echo "${CANN_KERNELS_URL}" > /tmp/kernels_url_file.txt && \
    echo "${CANN_NNAL_URL}" > /tmp/nnal_url_file.txt

# Install dependencies
RUN yum update -y && \
    yum install -y \
        gcc \
        gcc-c++ \
        make \
        cmake \
        unzip \
        zlib-devel \
        libffi-devel \
        openssl-devel \
        pciutils \
        net-tools \
        sqlite-devel \
        lapack-devel \
        gcc-gfortran \
        util-linux \
        findutils \
        curl \
        wget \
    && yum clean all \
    && rm -rf /var/cache/yum

RUN CANN_TOOLKIT_URL=$(cat /tmp/toolkit_url_file.txt) && \
    wget ${CANN_TOOLKIT_URL} -O ~/Ascend-cann-toolkit.run && \
    chmod +x ~/Ascend-cann-toolkit.run && \
    printf "Y\n" | ~/Ascend-cann-toolkit.run --install && \
    rm -f ~/Ascend-cann-toolkit.run
  
RUN CANN_KERNELS_URL=$(cat /tmp/kernels_url_file.txt) && \
    wget ${CANN_KERNELS_URL} -O ~/Ascend-cann-kernels.run && \
    chmod +x ~/Ascend-cann-kernels.run && \
    printf "Y\n" | ~/Ascend-cann-kernels.run --install && \
    rm -f ~/Ascend-cann-kernels.run

RUN export ASCEND_HOME_PATH=/usr/local/Ascend && \
    export ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit/latest && \
    export ASCEND_NNAE_HOME=/usr/local/Ascend/nnal && \
    CANN_NNAL_URL=$(cat /tmp/nnal_url_file.txt) && \
    wget ${CANN_NNAL_URL} -O ~/Ascend-cann-nnal.run && \
    chmod +x ~/Ascend-cann-nnal.run && \
    printf "Y\n" | ~/Ascend-cann-nnal.run --install && \
    rm -f ~/Ascend-cann-nnal.run; \
fi
    
# Stage 2: Copy results from previous stages
FROM ascendai/python:{{ dependence }} AS official

# Environment variables
ENV LD_LIBRARY_PATH=/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:${LD_LIBRARY_PATH}

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
COPY --from=cann-installer /usr/local/Ascend /usr/local/Ascend
COPY --from=cann-installer /etc/Ascend /etc/Ascend

# Set environment variables
RUN CANN_TOOLKIT_ENV_FILE="/usr/local/Ascend/ascend-toolkit/set_env.sh" && \
    CANN_NNAL_ENV_FILE="/usr/local/Ascend/nnal/atb/set_env.sh" && \
    DRIVER_LIBRARY_PATH="LD_LIBRARY_PATH=/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:\${LD_LIBRARY_PATH}" && \
    echo "export ${DRIVER_LIBRARY_PATH}" >> /etc/profile && \
    echo "export ${DRIVER_LIBRARY_PATH}" >> ~/.bashrc && \
    echo "source ${CANN_TOOLKIT_ENV_FILE}" >> /etc/profile && \
    echo "source ${CANN_TOOLKIT_ENV_FILE}" >> ~/.bashrc && \
    echo "source ${CANN_NNAL_ENV_FILE}" >> /etc/profile && \
    echo "source ${CANN_NNAL_ENV_FILE}" >> ~/.bashrc
    

ENTRYPOINT ["/bin/bash", "-c", "\
  source /usr/local/Ascend/ascend-toolkit/set_env.sh && \
  source /usr/local/Ascend/nnal/atb/set_env.sh; \
  exec \"$@\"", "--"]

