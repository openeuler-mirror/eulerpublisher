#!/bin/bash
echo -e "\n[STAGE] Prepare environment"
sudo apt-get update
sudo apt-get install -y tar xz-utils qemu shunit2
if [ docker info > /dev/null 2>&1 ]; then
    systemctl start docker
    echo "starting docker..."
fi

if [ which eulerpublisher > /dev/null 2>&1 ]; then
    sudo pip3 uninstall -y eulerpublisher > /dev/null 2>&1
fi

rm -rf eulerpublisher
git clone https://gitee.com/openeuler/eulerpublisher.git
cd eulerpublisher
pip3 uninstall -y eulerpublisher > /dev/null 2>&1 || true
rm -rf /usr/local/lib/python3.*/site-packages/eulerpublisher*
pip3 install -r ./requirements.txt > /dev/null 2>&1
pip3 install . > /dev/null 2>&1

set -e
# update list
VERSIONS=(
    "20.03-LTS-SP4"
    "22.03-LTS"
    "22.03-LTS-SP3"
    "22.03-LTS-SP4"
    "24.03-LTS"
    "24.03-LTS-SP1"
    "24.03-LTS-SP2"
    "24.03-LTS-SP3"
)

# publish updates
echo -e "\n[STAGE] Publish images"
sudo -E python3 update/container/base/update.py "${VERSIONS[@]}"

# clear cache
echo -e "\n[STAGE] Clear cache"
rm -rf /tmp/eulerpublisher/
exit 0