ARG BASE_VERSION = 3.9

FROM openeuler/openeuler:${BASE_VERSION}

RUN yum update -y && \
    yum install -y \
        curl \
    && yum clean all \
    && rm -rf /var/cache/yum  \
    && rm -rf /tmp/*
 
WORKDIR /app

COPY . /app

EXPOSE 8080

CMD ["bash"]