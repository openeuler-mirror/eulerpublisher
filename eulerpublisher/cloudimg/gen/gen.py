# -*- coding:utf-8 -*-
import click
import datetime
import subprocess
import os
import platform
import wget


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH
from eulerpublisher.publisher import OPENEULER_REPO


GEN_DATA_PATH = "/tmp/eulerpublisher/cloudimg/gen/data/"
DEFAULT_RPMLIST = EP_PATH + "config/cloudimg/gen/install_packages.txt"
CONFIG_FILE = EP_PATH + "config/cloudimg/gen/gen.cfg"
SCRIPT_PATH = EP_PATH + "config/cloudimg/script/"


class GenPublisher(pb.Publisher):
    def __init__(self, version="", arch="", rpmlist="", output=""):
        # 关键参数
        self.version = version.upper()
        # 获取支持的架构类型
        if arch != str(platform.machine()):
            raise TypeError(
                "Unsupported architecture "
                + arch
                + "while current host architecture is "
                + str(platform.machine())
            )
        self.arch = arch
        # 获取要预安装的软件包列表，不显示指定时安装默认包
        if not rpmlist:
            self.rpmlist = DEFAULT_RPMLIST
        else:
            self.rpmlist = os.path.abspath(rpmlist)
        # 构建生成的镜像名
        self.output = output

    def prepare(self):
        if not os.path.exists(GEN_DATA_PATH):
            os.makedirs(GEN_DATA_PATH, exist_ok=True)
        os.chdir(GEN_DATA_PATH)
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
                    click.echo("\nDownloading " + xz_file + "...")
                    wget.download(url)
                except Exception as err:
                    raise click.ClickException("[Prepare] " + str(err))
            if subprocess.call(["unxz", "-f", xz_file]):
                click.echo(click.style("\n[Prepare] failed", fg="red"))
                return pb.PUBLISH_FAILED
        click.echo("\n[Prepare] finished")
        return pb.PUBLISH_SUCCESS

    def build(self):
        input = "openEuler-" + self.version + "-" + self.arch + ".qcow2"
        time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # 默认输出保存为带有时间信息的qcow2格式
        if not self.output:
            self.output = (
                "openEuler-"
                + self.version
                + "-"
                + self.arch
                + "-"
                + time_str
                + ".qcow2"
            )
        script = SCRIPT_PATH + "gen_install.sh"
        args = [input, self.output, GEN_DATA_PATH, self.rpmlist, CONFIG_FILE]
        if subprocess.call(["sudo", "sh", script] + args):
            click.echo("\n[Build] finished")
            return pb.PUBLISH_FAILED
        click.echo("\n[Build] finished")
        return pb.PUBLISH_SUCCESS
