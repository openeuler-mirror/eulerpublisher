#!/bin/bash
python3 setup.py install
pip install eulerpublisher
pip3 install -r ./requirements.txt


set -e
# check for new cloud image versions and publish
echo -e "\n[STAGE] Check and publish cloud images"
sudo -E python3 update/image/update.py config/cloudimg/cloudimg.yaml

# clear cache
echo -e "\n[STAGE] Clear cache"
rm -rf /tmp/eulerpublisher_cloudimg_update/
exit 0
