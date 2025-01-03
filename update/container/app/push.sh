#!/bin/sh
set -e

if [ "$state" != "merged" ]; then
    exit 0
fi
# start docker
if [ docker info > /dev/null 2>&1 ]; then
    systemctl start docker
    echo "starting docker..."
fi
# install newest eulerpublisher
if [ which eulerpublisher > /dev/null 2>&1 ]; then
    sudo pip3 uninstall -y eulerpublisher > /dev/null 2>&1
fi
rm -rf eulerpublisher/
git clone https://gitee.com/openeuler/eulerpublisher.git
cd eulerpublisher
pip3 install -r ./requirements.txt > /dev/null 2>&1
python3 setup.py install > /dev/null 2>&1
# publish to hubs
sudo -E python3 update/container/app/update.py \
	-pr ${giteePullRequestId} \
    -sr ${giteeRepoName} \
    -br ${giteeTargetBranch} \
    -su ${giteeTargetRepoUrl} \
    -op push