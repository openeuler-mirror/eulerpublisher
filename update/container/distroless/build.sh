#!/bin/bash
set -e

PKGS=("tar" "xz-utils" "qemu" "shunit2")

if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y "${PKGS[@]}"

elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y tar xz qemu shunit2

elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y tar xz qemu shunit2

elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y tar xz qemu shunit2

else
    echo "[ERROR] No supported package manager found (apt, dnf, yum, zypper)"
    exit 1
fi

# clear unused resources
echo "清理缓存..."
docker image prune -f > /dev/null 2>&1
docker container prune -f > /dev/null 2>&1
docker network prune -f > /dev/null 2>&1
docker system prune -af > /dev/null 2>&1
docker volume rm $(docker volume ls -q) --force > /dev/null 2>&1 || true
docker system df
echo "清理完成!"

if [ docker info > /dev/null 2>&1 ]; then
    systemctl start docker
    echo "starting docker..."
fi

if [ which eulerpublisher > /dev/null 2>&1 ]; then
    sudo pip3 uninstall -y eulerpublisher > /dev/null 2>&1
fi

cd ../
rm -rf eulerpublisher/
git clone https://gitee.com/openeuler/eulerpublisher.git
cd eulerpublisher
pip3 install . > /dev/null 2>&1

sudo -E python3 update/container/distroless/update.py