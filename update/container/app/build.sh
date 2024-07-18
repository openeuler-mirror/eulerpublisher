#!/bin/bash

if [ docker info > /dev/null 2>&1 ]; then
    systemctl start docker
    echo "starting docker..."
fi

if [ which eulerpublisher > /dev/null 2>&1 ]; then
    sudo pip3 uninstall -y eulerpublisher
fi

rm -rf eulerpublisher/
git clone https://gitee.com/openeuler/eulerpublisher.git
cd eulerpublisher
pip3 install -r ./requirements.txt
python3 setup.py install

sudo -E python3 update/container/app/update.py \
	-pr ${prid} \
    -sr ${repo} \
    -su ${scodeurl} \
    -br ${branch} \
    -op check