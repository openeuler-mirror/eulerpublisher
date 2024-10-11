#!/usr/bin/env bash

set -e

# 安装eulerpublisher
sudo python3 setup.py install --record install_log.txt

# 安装python依赖
sudo pip install -r requirements.txt

# 安装qemu
sudo yum install -y qemu-img

# 创建工具集目录
mkdir -p utils

# 安装docker
if [[ ! -e "utils/docker.tar.gz" ]]; then
    if [[ "$(uname -m)" == "aarch64" ]]; then
        wget https://download.docker.com/linux/static/stable/aarch64/docker-24.0.9.tgz -O utils/docker.tar.gz
    elif [[ "$(uname -m)" == "x86_64" ]]; then
        wget https://download.docker.com/linux/static/stable/x86_64/docker-24.0.9.tgz -O utils/docker.tar.gz
    else
        echo "Unrecognized arch $(uname -m)"
        exit 1
    fi
fi
mkdir -p utils/docker
tar -zxf utils/docker.tar.gz -C utils/docker --strip-components=1
sudo cp -p utils/docker/* /usr/local/bin
if ! sudo grep -q docker /etc/group; then
    sudo groupadd docker || true
fi
if [[ ! -z ${USER:-} ]]; then
    sudo usermod -aG docker $USER || true
else
    sudo usermod -aG docker openeuler || true
fi

# 安装slim
curl -sL https://raw.githubusercontent.com/slimtoolkit/slim/master/scripts/install-slim.sh | sudo -E bash -

# 安装云厂商命令行工具
if [[ "$(uname -m)" == "aarch64" ]]; then
    if [[ ! -e "utils/awsutil.zip" ]]; then
        wget "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -O utils/awsutil.zip
    fi
    if [[ ! -e "utils/obsutil.tar.gz" ]]; then
        wget "https://obs-community.obs.cn-north-1.myhuaweicloud.com/obsutil/current/obsutil_linux_arm64.tar.gz" -O utils/obsutil.tar.gz
    fi
    if [[ ! -e "utils/coscli" ]]; then
        wget "https://cosbrowser.cloud.tencent.com/software/coscli/coscli-v1.0.1-linux-arm64" -O utils/coscli
    fi
    if [[ ! -e "utils/ossutil.zip" ]]; then
        wget "https://gosspublic.alicdn.com/ossutil/1.7.19/ossutil-v1.7.19-linux-arm64.zip" -O utils/ossutil.zip
    fi
elif [[ "$(uname -m)" == "x86_64" ]]; then
    if [[ ! -e "utils/awsutil.zip" ]]; then
        wget "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -O utils/awsutil.zip
    fi 
    if [[ ! -e "utils/obsutil.tar.gz" ]]; then
        wget "https://obs-community.obs.cn-north-1.myhuaweicloud.com/obsutil/current/obsutil_linux_amd64.tar.gz" -O utils/obsutil.tar.gz
    fi
    if [[ ! -e "utils/coscli" ]]; then
        wget "https://cosbrowser.cloud.tencent.com/software/coscli/coscli-v1.0.1-linux-amd64" -O utils/coscli
    fi
    if [[ ! -e "utils/ossutil.zip" ]]; then
        wget "https://gosspublic.alicdn.com/ossutil/1.7.19/ossutil-v1.7.19-linux-amd64.zip" -O utils/ossutil.zip
    fi
else
    echo "Unrecognized arch $(uname -m)"
    exit 1
fi
unzip utils/awsutil.zip -d utils
sudo bash utils/aws/install
mkdir -p utils/obsutil
tar -xvf utils/obsutil.tar.gz -C utils/obsutil --strip-components=1
sudo cp -p utils/obsutil/obsutil /usr/local/bin
chmod 755 utils/coscli
sudo cp -p utils/coscli /usr/local/bin
mkdir -p utils/ossutil
unzip -j utils/ossutil.zip -d utils/ossutil
sudo cp -p utils/ossutil/ossutil /usr/local/bin

# 安装shUnit2
if [[ ! -e "utils/shunit2.tar.gz" ]]; then
    wget https://github.com/kward/shunit2/archive/refs/tags/v2.1.8.tar.gz -O utils/shunit2.tar.gz
fi
mkdir -p /usr/share/shunit2
tar -xvf utils/shunit2.tar.gz -C /usr/share/shunit2 --strip-components=1
