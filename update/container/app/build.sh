#!/bin/bash
set -e
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

rm -rf splitter/
dnf install -y python3-dnf git python3-pip cpio
git clone https://gitee.com/openeuler/splitter.git
cd splitter
pip3 install . > /dev/null 2>&1

cd ../
rm -rf eulerpublisher/
git clone https://gitee.com/openeuler/eulerpublisher.git
cd eulerpublisher
pip3 install -r ./requirements.txt > /dev/null 2>&1
python3 setup.py install > /dev/null 2>&1

sudo -E python3 update/container/app/update.py \
	-pr ${prid} \
    -sr ${repo} \
    -su ${scodeurl} \
    -br ${branch} \
    -op check