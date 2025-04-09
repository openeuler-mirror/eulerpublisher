#!/usr/bin/env bash

set -e

if [[ "$(uname -m)" == "x86_64" ]]; then
    AWSCLI_ARCH="x86_64"
    OBSUTIL_ARCH="amd64"
    COSCLI_ARCH="amd64"
    OSSUTIL_ARCH="amd64"
elif [[ "$(uname -m)" == "aarch64" ]]; then
    AWSCLI_ARCH="aarch64"
    OBSUTIL_ARCH="arm64"
    COSCLI_ARCH="arm64"
    OSSUTIL_ARCH="arm64"
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
cd utils

# 安装docker
if [[ ! $(which docker) ]]; then
    curl -sL https://raw.githubusercontent.com/cnrancher/euler-packer/refs/heads/main/scripts/others/install-docker.sh | sudo -E bash - 
fi

# 安装公有云厂商命令行工具
if [[ ! $(which aws) ]]; then
    wget https://awscli.amazonaws.com/awscli-exe-linux-${AWSCLI_ARCH}.zip -O awsutil.zip
    unzip awsutil.zip
    sudo bash aws/install
fi

if [[ ! $(which obsutil) ]]; then
    wget https://obs-community.obs.cn-north-1.myhuaweicloud.com/obsutil/current/obsutil_linux_${OBSUTIL_ARCH}.tar.gz -O obsutil.tar.gz
    mkdir -p obsutil
    tar -xvf obsutil.tar.gz -C obsutil --strip-components=1
    sudo cp -p obsutil/obsutil /usr/local/bin
fi

if [[ ! $(which coscli) ]]; then
    wget https://cosbrowser.cloud.tencent.com/software/coscli/coscli-v1.0.1-linux-${COSCLI_ARCH} -O coscli
    chmod 755 coscli
    sudo cp -p coscli /usr/local/bin
fi

if [[ ! $(which ossutil) ]]; then
    wget https://gosspublic.alicdn.com/ossutil/1.7.19/ossutil-v1.7.19-linux-${OSSUTIL_ARCH}.zip -O ossutil.zip
    mkdir -p ossutil
    unzip -j ossutil.zip -d ossutil
    sudo cp -p ossutil/ossutil /usr/local/bin
fi

# 安装shUnit2
if [[ ! -e "/usr/share/shunit2" ]]; then
    wget https://github.com/kward/shunit2/archive/refs/tags/v2.1.8.tar.gz -O shunit2.tar.gz
    mkdir -p /usr/share/shunit2
    tar -xvf shunit2.tar.gz -C /usr/share/shunit2 --strip-components=1
fi
