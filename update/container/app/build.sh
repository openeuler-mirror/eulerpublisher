#!/bin/bash
set -euo pipefail

for v in prid repo scodeurl branch; do
    [ -n "${!v:-}" ] || { echo "ERROR: $v is empty/unset" >&2; exit 1; }
done

if ! docker info >/dev/null 2>&1; then
    echo "docker 未运行，启动中..."
    sudo systemctl start docker
    for _ in $(seq 1 30); do
        docker info >/dev/null 2>&1 && break
        sleep 2
    done
    docker info >/dev/null 2>&1 || { echo "ERROR: docker 启动失败" >&2; exit 1; }
fi

echo "清理缓存..."
docker system prune -af --volumes || true
docker system df
echo "清理完成!"

rm -rf splitter eulerpublisher
sudo dnf install -y python3-dnf git python3-pip cpio

git clone https://gitcode.com/openeuler/splitter.git
sudo pip3 install ./splitter

git clone https://gitcode.com/openeuler/eulerpublisher.git
cd eulerpublisher

pip3      uninstall -y eulerpublisher >/dev/null 2>&1 || true
sudo pip3 uninstall -y eulerpublisher >/dev/null 2>&1 || true

sudo pip3 install -r ./requirements.txt
sudo pip3 install .

sudo env "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    sh -c 'command -v eulerpublisher' >/dev/null \
    || { echo "ERROR: root 环境下找不到 eulerpublisher" >&2; exit 1; }
sudo /usr/bin/python3 -c 'import eulerpublisher' 2>/dev/null \
    || { echo "ERROR: root 的 python3 里 import eulerpublisher 失败" >&2; exit 1; }

sudo env "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    /usr/bin/python3 update/container/app/update.py \
    -pr "${prid}" \
    -sr "${repo}" \
    -su "${scodeurl}" \
    -br "${branch}" \
    -op check
