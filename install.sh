#!/usr/bin/env bash

set -e

if [[ "$(uname -m)" == "aarch64" ]]; then
  DOCKER_ARCH="aarch64"
elif [[ "$(uname -m)" == "x86_64" ]]; then
  DOCKER_ARCH="x86_64"
else
  echo "Unrecognized arch $(uname -m)"
  exit 1
fi

# 安装eulerpublisher
sudo python3 setup.py install --record install_log.txt

# 安装qemu
sudo yum install -y qemu-img

# 安装docker
if [[ ! -e "docker.tar.gz" ]]; then
  wget https://download.docker.com/linux/static/stable/${DOCKER_ARCH}/docker-24.0.9.tgz -O docker.tar.gz
fi
tar -zxf ./docker.tar.gz
sudo cp -p docker/* /usr/bin
if [[ ! -z ${USER:-} ]]; then
  sudo usermod -aG docker $USER || true
else
  sudo usermod -aG docker openeuler || true
fi

# 安装slim
curl -sL https://raw.githubusercontent.com/slimtoolkit/slim/master/scripts/install-slim.sh | sudo -E bash -

# 安装python依赖
sudo pip install -r ./requirements.txt

# 安装shUnit2
if [[ ! -e "shunit2.tar.gz" ]]; then
curl -fSL -o shunit2.tar.gz https://github.com/kward/shunit2/archive/refs/tags/v2.1.8.tar.gz
fi
mkdir -p /usr/share/shunit2
tar -xvf shunit2.tar.gz -C /usr/share/shunit2 --strip-components=1
