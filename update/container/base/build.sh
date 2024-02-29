#!/bin/bash
echo -e "\n[STAGE] Prepare environment"
sudo apt-get update
sudo apt-get install -y tar xz-utils qemu shunit2
if [[docker info > /dev/null 2>&1]]; then
    systemctl start docker
    echo "starting docker..."
fi

echo -e "\n[STAGE] Install eulerpublisher"
if [[which eulerpublisher > /dev/null 2>&1]]; then
    sudo pip3 uninstall -y eulerpublisher
fi
git clone -b rebuild https://gitee.com/lu-wei-army/eulerpublisher.git
cd eulerpublisher
pip3 install -r ./requirement.txt
python3 setup.py install

set -e
# update list
VERSIONS=(
    "20.03-LTS-SP1"
    "20.03-LTS-SP3"
    "20.03-LTS-SP4"
    "22.03-LTS"
    "22.03-LTS-SP1"
    "22.03-LTS-SP2"
    "22.03-LTS-SP3"
)

# publish updates
echo -e "\n[STAGE] Publish images"
sudo -E python3 update/container/base/update.py "${VERSIONS[@]}"

# clear cache
echo -e "\n[STAGE] Clear cache"
rm -rf /tmp/eulerpublisher/
exit 0