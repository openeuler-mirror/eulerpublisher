#!/bin/bash
set -e
# clear unused resources
echo "清理缓存..."
docker image prune -f
docker container prune -f
docker network prune -f
docker volume prune -f
docker system prune -af
docker system df
echo "清理完成!"

if [ docker info > /dev/null 2>&1 ]; then
    systemctl start docker
    echo "starting docker..."
fi

if [ which eulerpublisher > /dev/null 2>&1 ]; then
    sudo pip3 uninstall -y eulerpublisher > /dev/null 2>&1
fi

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