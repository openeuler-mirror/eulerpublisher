#!/usr/bin/env bash

set -e

if [[ "$(uname -m)" == "x86_64" ]]; then
    ARCH="x86_64"
elif [[ "$(uname -m)" == "aarch64" ]]; then
    ARCH="aarch64"
else
    echo "Unrecognized arch $(uname -m)"
    exit 1
fi

# 安装eulerpublisher
sudo python3 setup.py install --record install_log.txt

# 安装python依赖
sudo pip install -r requirements.txt

# 安装qemu
sudo yum install -y qemu-img

# 创建工具集目录
mkdir -p utils

# 安装docker
if [[ ! $(which docker) ]]; then
    wget https://download.docker.com/linux/static/stable/${ARCH}/docker-24.0.9.tgz -O utils/docker.tar.gz
    mkdir -p utils/docker
    tar -zxf utils/docker.tar.gz -C utils/docker --strip-components=1
    sudo cp -p utils/docker/* /usr/local/bin
    if [[ ! $(sudo grep -q docker /etc/group) ]]; then
        sudo groupadd docker || true
    fi
    if [[ ! -z ${USER:-} ]]; then
        sudo usermod -aG docker $USER || true
    else
        sudo usermod -aG docker openeuler || true
    fi
fi

# 安装slim
if [[ ! $(which slim) ]]; then
    curl -sL https://raw.githubusercontent.com/slimtoolkit/slim/master/scripts/install-slim.sh | sudo -E bash -
fi

# 安装公有云厂商命令行工具
if [[ ! $(which aws) ]]; then
    wget https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip -O utils/awsutil.zip
    unzip utils/awsutil.zip -d utils
    sudo bash utils/aws/install
fi

if [[ "$(uname -m)" == "x86_64" ]]; then
    ARCH="amd64"
elif [[ "$(uname -m)" == "aarch64" ]]; then
    ARCH="arm64"
else
    echo "Unrecognized arch $(uname -m)"
    exit 1
fi

if [[ ! $(which obsutil) ]]; then
    wget https://obs-community.obs.cn-north-1.myhuaweicloud.com/obsutil/current/obsutil_linux_${ARCH}.tar.gz -O utils/obsutil.tar.gz
    mkdir -p utils/obsutil
    tar -xvf utils/obsutil.tar.gz -C utils/obsutil --strip-components=1
    sudo cp -p utils/obsutil/obsutil /usr/local/bin
fi

if [[ ! $(which coscli) ]]; then
    wget https://cosbrowser.cloud.tencent.com/software/coscli/coscli-v1.0.1-linux-${ARCH} -O utils/coscli
    chmod 755 utils/coscli
    sudo cp -p utils/coscli /usr/local/bin
fi

if [[ ! $(which ossutil) ]]; then
    wget https://gosspublic.alicdn.com/ossutil/1.7.19/ossutil-v1.7.19-linux-${ARCH}.zip -O utils/ossutil.zip
    mkdir -p utils/ossutil
    unzip -j utils/ossutil.zip -d utils/ossutil
    sudo cp -p utils/ossutil/ossutil /usr/local/bin
fi

# 安装shUnit2
if [[ ! -e "/usr/share/shunit2" ]]; then
    wget https://github.com/kward/shunit2/archive/refs/tags/v2.1.8.tar.gz -O utils/shunit2.tar.gz
    mkdir -p /usr/share/shunit2
    tar -xvf utils/shunit2.tar.gz -C /usr/share/shunit2 --strip-components=1
fi