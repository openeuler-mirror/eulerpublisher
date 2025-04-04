# coding=utf-8
import os


EP_PATH = None
OPENEULER_REPO = "http://repo.openeuler.org/"
OPENEULER_DOCKERFILE = "https://gitee.com/openeuler/openeuler-docker-images/raw/master/Base/openeuler/Dockerfile"

paths = [
    os.path.dirname(os.__file__) + "/" + "../../etc/eulerpublisher/",
    "/usr/local/etc/eulerpublisher/",
    "/usr/etc/eulerpublisher/",
    "/etc/eulerpublisher/",
]

for path in paths:
    if os.path.exists(path):
        EP_PATH = path
        break
