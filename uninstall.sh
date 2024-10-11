#!/usr/bin/env bash

set -e

# 卸载eulerpublisher 
cat install_log.txt | sudo xargs rm -rf
rm -rf install_log.txt
rm -rf build eulerpublisher.egg-info .eggs

# 卸载python依赖 
sudo pip uninstall -yr requirements.txt

# 卸载qemu
sudo yum autoremove -y qemu-img

# 卸载docker
sudo rm -rf /usr/local/bin/containerd   \
            /usr/local/bin/ctr          \
            /usr/local/bin/dockerd      \
            /usr/local/bin/docker-proxy \
            /usr/local/bin/docker       \
            /usr/local/bin/docker-init  \
            /usr/local/bin/runc         \
            /usr/local/bin/containerd-shim-runc-v2  

# 卸载云厂商命令行工具
sudo rm -rf /usr/local/bin/coscli  \
            /usr/local/bin/obsutil \
            /usr/local/bin/ossutil \
            /usr/local/aws-cli     \
            /usr/local/bin/aws     \
            /usr/local/bin/aws_completer

# 卸载slim
sudo rm -rf /usr/local/bin/slim \
            /usr/local/bin/slim-sensor

# 卸载shUnit2
sudo rm -rf /usr/share/shunit2

# 清理工具集
rm -rf utils
