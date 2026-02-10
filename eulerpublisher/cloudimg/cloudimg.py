# -*- coding:utf-8 -*-
import click
import subprocess
import os
import platform
import yaml
import wget

import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH, logger, get_temp_dir
from eulerpublisher.publisher import OPENEULER_REPO

from eulerpublisher.cloudimg.vendor.huawei import push_huawei
from eulerpublisher.cloudimg.vendor.tencent import push_tencent
from eulerpublisher.cloudimg.vendor.alibaba import push_alibaba
from eulerpublisher.cloudimg.vendor.aws import push_aws

DATA_PATH = get_temp_dir("cloudimg", "data") + os.sep
SCRIPT_PATH = EP_PATH + "config/cloudimg/script/"
RESOURCE_PATH = EP_PATH + "config/cloudimg/resource/"
DEFAULT_RPMLIST = RESOURCE_PATH + "install_packages.txt"
CLOUD_INIT_CONFIG = RESOURCE_PATH + "openeuler.cfg"


class CloudimgPublisher(pb.Publisher):
    def __init__(self, config_file, target=""):
        # 加载 YAML 配置文件
        self.config = self._load_config(config_file)
        # 目标云厂商
        self.target = target
        # 镜像版本号
        self.version = self.config["version"].upper()
        # 镜像架构类型
        arch = self.config["arch"]
        if arch != str(platform.machine()):
            raise TypeError(
                "Unsupported architecture "
                + arch
                + " while current host architecture is "
                + str(platform.machine())
            )
        self.arch = arch
        # 获取要预安装的软件包列表，不指定时安装默认包
        rpmlist = self.config.get("rpmlist", "")
        if not rpmlist:
            self.rpmlist = DEFAULT_RPMLIST
        else:
            self.rpmlist = os.path.abspath(rpmlist)
        # 从 targets 配置中读取目标云厂商的 ak、sk、bucket 和 region
        self.ak = ""
        self.sk = ""
        self.bucket = ""
        self.region = ""
        if target and "targets" in self.config and target in self.config["targets"]:
            target_cfg = self.config["targets"][target]
            self.ak = target_cfg.get("ak", "")
            self.sk = target_cfg.get("sk", "")
            self.bucket = target_cfg.get("bucket", "")
            self.region = target_cfg.get("region", "")

    def _load_config(self, config_file):
        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    def _detect_image(self):
        """自动检测 output 目录下最新的镜像文件"""
        output_dir = DATA_PATH + "output/"
        if not os.path.exists(output_dir):
            return None
        files = [f for f in os.listdir(output_dir) if os.path.isfile(output_dir + f)]
        if not files:
            return None
        files.sort(key=lambda f: os.path.getmtime(output_dir + f), reverse=True)
        return files[0]

    def prepare(self):
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH, exist_ok=True)
        os.chdir(DATA_PATH)
        qcow2_file = "openEuler-" + self.version + "-" + self.arch + ".qcow2"
        xz_file = "openEuler-" + self.version + "-" + self.arch + ".qcow2.xz"
        if not os.path.exists(qcow2_file):
            if not os.path.exists(xz_file):
                url = (
                    OPENEULER_REPO
                    + "openEuler-"
                    + self.version
                    + "/"
                    + "virtual_machine_img"
                    + "/"
                    + self.arch
                    + "/"
                    + xz_file
                )
                try:
                    logger.info("[Prepare] Downloading '%s'..." % xz_file)
                    wget.download(url)
                except Exception as err:
                    raise err
            if subprocess.call(["unxz", "-f", xz_file]):
                logger.error("[Prepare] Failed to unxz '%s'." % xz_file)
                return pb.PUBLISH_FAILED
        logger.info("[Prepare] Finished.")
        return pb.PUBLISH_SUCCESS

    def build(self):
        qcow2_file = "openEuler-" + self.version + "-" + self.arch + ".qcow2"
        if not os.path.exists(DATA_PATH + qcow2_file):
            logger.error("[Build] Failed to find original image '%s'." % qcow2_file)
            return pb.PUBLISH_FAILED

        build_scripts = {
            "huawei": "gen_build.sh",
            "tencent": "gen_build.sh",
            "alibaba": "gen_build.sh",
            "aws": "aws_build.sh",
            "azure": "azure_build.sh"
        }
        script = SCRIPT_PATH + build_scripts[self.target]
        args = [qcow2_file, DATA_PATH, CLOUD_INIT_CONFIG, self.rpmlist]
        if subprocess.call(["sudo", "sh", script] + args):
            logger.error("[Build] Failed to build cloud image.")
            return pb.PUBLISH_FAILED
        logger.info("[Build] Finished.")
        return pb.PUBLISH_SUCCESS

    def push(self):
        # 自动检测最新的镜像文件
        image = self._detect_image()
        if not image:
            logger.error("[Push] Failed to find cloud image in output directory.")
            return pb.PUBLISH_FAILED
        logger.info("[Push] Detected image file: '%s'" % image)

        push_functions = {
            "huawei": push_huawei,
            "tencent": push_tencent,
            "alibaba": push_alibaba,
            "aws": push_aws,
        }
        if self.target in push_functions:
            push_functions[self.target](self.arch, self.version, self.ak, self.sk, self.bucket, self.region, image)
        else:
            logger.error("[Push] Unsupported cloud provider '%s'." % self.target)
            return pb.PUBLISH_FAILED

        logger.info("[Push] Finished.")
        return pb.PUBLISH_SUCCESS

    def publish(self):
        if self.prepare() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        if self.build() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        return self.push()
