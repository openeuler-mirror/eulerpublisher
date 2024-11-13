#!/bin/sh
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
	-pr ${giteePullRequestId} \
    -sr ${giteeRepoName} \
    -br ${giteeTargetBranch} \
    -su ${giteeTargetRepoUrl} \
    -op push