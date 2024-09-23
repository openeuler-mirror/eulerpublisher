#!/usr/bin/env bash

set -e

# 卸载eulerpublisher 
cat install_log.txt | sudo xargs rm -rf
rm -rf install_log.txt
rm -rf build eulerpublisher.egg-info

# 卸载qemu
sudo yum autoremove -y qemu-img

# 卸载docker
for bin in $(ls ./docker)
do
  sudo rm -rf /usr/bin/$bin
done
rm -rf docker

# 卸载slim
sudo rm -rf /usr/local/bin/slim /usr/local/bin/slim-sensor

# 卸载python依赖 
sudo pip uninstall -yr ./requirements.txt

# 卸载shUnit2
sudo rm -rf /usr/share/shunit2