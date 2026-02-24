# coding=utf-8
import atexit
import logging
import os
import shutil
import tempfile


EP_PATH = None
EP_LOG_DIR = "/tmp/"
EP_TMP_DIR = ""
OPENEULER_REPO = "https://repo.openeuler.org/"
OPENEULER_DOCKERFILE = "https://gitee.com/openeuler/openeuler-docker-images/raw/master/Base/openeuler/Dockerfile"

if os.environ.get('EP_LOG_DIR'):
    EP_LOG_DIR = os.environ.get('EP_LOG_DIR')

_auto_tmp = False
if os.environ.get("EP_TMP_DIR"):
    EP_TMP_DIR = os.environ.get("EP_TMP_DIR")
else:
    EP_TMP_DIR = tempfile.mkdtemp(prefix="eulerpublisher_")
    _auto_tmp = True

os.makedirs(EP_TMP_DIR, exist_ok=True)


def _cleanup_tmp():
    if _auto_tmp and os.path.isdir(EP_TMP_DIR):
        shutil.rmtree(EP_TMP_DIR, ignore_errors=True)


atexit.register(_cleanup_tmp)

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

AVAILABLE_ARCHES = {
    "x86_64": "amd64",
    "aarch64": "arm64",
    "loongarch64": "loong64"
}

DEFAULT_APP_ARCHES = {
    "x86_64": "amd64",
    "aarch64": "arm64"
}

class Logger:
    def __init__(self, name="eulerpublisher", level=logging.INFO):
        """ Initialize logger """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create stream handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        #  Create file handler
        fh = logging.FileHandler(os.path.join(EP_LOG_DIR, 'eulerpublisher.log'))
        fh.setLevel(level)
        # Set logging format
        formatter = logging.Formatter('%(asctime)s-%(pathname)s[line:%(lineno)d]-%(levelname)s: %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # Add handler to logger
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def debug(self, msg):
        self.logger.debug(msg, stacklevel=2)

    def info(self, msg):
        self.logger.info(msg, stacklevel=2)

    def warning(self, msg):
        self.logger.warning(msg, stacklevel=2)

    def error(self, msg):
        self.logger.error(msg, stacklevel=2)

    def critical(self, msg):
        self.logger.critical(msg, stacklevel=2)

logger = Logger()


def get_temp_dir(*parts, create=False):
    path = os.path.join(EP_TMP_DIR, *parts)
    if create:
        os.makedirs(path, exist_ok=True)
    return path