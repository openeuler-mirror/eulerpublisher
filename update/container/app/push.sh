#!/bin/sh

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
    sudo pip3 uninstall -y eulerpublisher
fi
rm -rf eulerpublisher/
git clone https://gitee.com/openeuler/eulerpublisher.git
cd eulerpublisher
pip3 install -r ./requirements.txt
python3 setup.py install
# publish to hubs
sudo -E python3 update/container/app/update.py \
	-pr ${giteePullRequestIid} \
    -sr ${giteeRepoName} \
    -su ${giteeSourceRepoUrl} \
    -br ${giteeSourceBranch} \
    -op push