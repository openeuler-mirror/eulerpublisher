# coding=utf-8
import sys
import os
import re
import subprocess
import yaml
import requests
import shutil
from bs4 import BeautifulSoup


MAX_REQUEST_COUNT = 20
VERSION_PATTERN = re.compile(r'^openEuler-\d+')
REPO_URL = "https://repo.openeuler.org/"
PUBLISHED_VERSIONS_FILE = "/tmp/eulerpublisher/cloudimg/published_versions.txt"
# 固定临时目录，确保多次 publish 调用共享同一个数据目录（避免重复下载）
EP_TMP_DIR = "/tmp/eulerpublisher_cloudimg_update"


def request(url):
    cnt = 0
    response = None
    while (not response) and (cnt < MAX_REQUEST_COUNT):
        try:
            response = requests.get(url=url, timeout=30)
        except Exception:
            pass
        cnt += 1
    return response


def get_repo_versions():
    """从 repo.openeuler.org 获取所有 openEuler-* 版本目录名"""
    response = request(REPO_URL)
    if not response:
        print("ERROR: Failed to request %s" % REPO_URL, file=sys.stderr)
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('tbody')
    if not table:
        print("ERROR: Failed to parse repo page.", file=sys.stderr)
        return []
    versions = []
    for row in table.find_all('tr'):
        link = row.find('td', class_='link')
        if link and VERSION_PATTERN.match(link.get_text()):
            dirname = link.get_text().strip().rstrip('/')
            # 去掉 openEuler- 前缀，得到版本号如 24.03-LTS-SP2
            version = dirname.replace('openEuler-', '', 1)
            versions.append(version)
    return versions


def check_virtual_machine_img(version):
    """检查该版本是否包含 virtual_machine_img 子目录"""
    url = REPO_URL + "openEuler-" + version + "/virtual_machine_img/"
    response = request(url)
    if response and response.status_code == 200:
        return True
    return False


def load_published_versions(filepath):
    """从本地文件加载已发布版本列表"""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r") as f:
        versions = set()
        for line in f:
            line = line.strip()
            if line:
                versions.add(line)
        return versions


def save_published_versions(filepath, versions):
    """保存已发布版本列表到本地文件"""
    dirpath = os.path.dirname(filepath)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, "w") as f:
        for version in sorted(versions):
            f.write(version + "\n")


def update_config_version(config_file, new_version):
    """修改 cloudimg.yaml 中的 version 字段"""
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    config["version"] = new_version
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def get_targets(config_file):
    """读取 cloudimg.yaml 中配置的所有云厂商"""
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    targets = config.get("targets", {})
    return list(targets.keys()) if targets else []


def publish_cloudimg(config_file, target):
    """调用 eulerpublisher cloudimg publish 发布云镜像"""
    env = os.environ.copy()
    env["EP_TMP_DIR"] = EP_TMP_DIR

    # 查找 eulerpublisher 命令路径
    eulerpublisher_cmd = shutil.which("eulerpublisher")
    if not eulerpublisher_cmd:
        # 如果在 PATH 中找不到，尝试在 python 的 bin 目录中查找
        python_bin_dir = os.path.dirname(sys.executable)
        eulerpublisher_path = os.path.join(python_bin_dir, "eulerpublisher")
        if os.path.exists(eulerpublisher_path):
            eulerpublisher_cmd = eulerpublisher_path

    cmd = [eulerpublisher_cmd, "cloudimg", "publish", "-c", config_file, "-t", target]
    ret = subprocess.call(cmd, env=env)
    return ret


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("ERROR: Usage: python3 update.py <config_file>", file=sys.stderr)
        sys.exit(1)

    config_file = sys.argv[1]
    if not os.path.exists(config_file):
        print("ERROR: Config file not found: %s" % config_file, file=sys.stderr)
        sys.exit(1)

    # 1. 获取所有云厂商 targets
    targets = get_targets(config_file)
    if not targets:
        print("ERROR: No targets configured in %s" % config_file, file=sys.stderr)
        sys.exit(1)
    print("INFO: Configured targets: %s" % ", ".join(targets))

    # 2. 获取 repo 中所有 openEuler 版本
    print("INFO: Fetching versions from %s ..." % REPO_URL)
    repo_versions = get_repo_versions()
    if not repo_versions:
        print("ERROR: No versions found on repo.", file=sys.stderr)
        sys.exit(1)
    print("INFO: Found %d versions on repo." % len(repo_versions))

    # 3. 过滤出包含 virtual_machine_img 的版本
    vm_versions = []
    for version in repo_versions:
        if check_virtual_machine_img(version):
            vm_versions.append(version)
    print("INFO: %d versions have virtual_machine_img." % len(vm_versions))

    # 4. 加载已发布版本记录
    published = load_published_versions(PUBLISHED_VERSIONS_FILE)
    print("INFO: Previously published: %d versions." % len(published))

    # 5. 对比得到新增版本
    new_versions = [v for v in vm_versions if v not in published]
    if not new_versions:
        print("INFO: No new versions to publish.")
        sys.exit(0)
    print("INFO: New versions to publish: %s" % ", ".join(new_versions))

    # 6. 对每个新版本，遍历所有 targets 执行 publish
    for version in new_versions:
        print("INFO: Publishing cloud image for version %s ..." % version)
        update_config_version(config_file, version)
        all_success = True
        for target in targets:
            print("INFO:   -> target: %s" % target)
            if publish_cloudimg(config_file, target) != 0:
                print("ERROR: Failed to publish %s to %s." % (version, target), file=sys.stderr)
                all_success = False
            else:
                print("INFO: Successfully published %s to %s." % (version, target))
        if all_success:
            published.add(version)

    # 7. 保存已发布版本记录
    save_published_versions(PUBLISHED_VERSIONS_FILE, published)
    print("INFO: Done. Published versions record updated.")
    sys.exit(0)
