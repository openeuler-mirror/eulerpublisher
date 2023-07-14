# coding=utf-8
import click
import datetime
import docker
import os
import re
import shutil
import subprocess
import wget

import eulerpublisher.publisher.publisher as pb

DOCKERFILE_PATH = os.path.dirname(os.__file__) + '/' \
    "../../etc/eulerpublisher/container/Dockerfile"
CACHE_DATA_PATH = "/tmp/eulerpublisher/container/"


# 运行容器，执行command命令，运行结果与预期结果param进行对比，返回成功 0/失败 1
def _run(tag="", cmd="", param=""):
    ret = pb.PUBLISH_FAILED
    client = docker.from_env()
    container = client.create_container(image=tag, command=cmd, detach=True)
    client.start(container)

    subprocess.call("docker logs " + container["Id"] + " >>logs.txt",
                    shell=True)
    logs = open("logs.txt")
    for line in logs:
        if param in line:
            ret = pb.PUBLISH_SUCCESS
    logs.close()
    subprocess.call(["rm", "-rf", "logs.txt"])
    client.stop(container)
    return ret


class ContainerPublisher(pb.Publisher):
    def __init__(self,
                 repo=None,
                 version=None,
                 registry=None,
                 dockerfile=None):
        self.repo = repo
        self.version = version
        self.registry = registry
        self.dockerfile = dockerfile
        if not self.dockerfile:
            self.dockerfile = ""

    def prepare(self):
        # 创建以版本号命名的目录
        os.makedirs(CACHE_DATA_PATH, exist_ok=True)
        os.chdir(CACHE_DATA_PATH)
        os.makedirs(self.version, exist_ok=True)
        shutil.copy2(DOCKERFILE_PATH, self.version + "/Dockerfile")
        os.chdir(self.version)

        for arch in pb.ARCHS:
            if arch == "x86_64":
                docker_arch = "amd64"
            elif arch == "aarch64":
                docker_arch = "arm64"

            # 下载文件
            if not os.path.exists("openEuler-docker." + arch + ".tar.xz"):
                download_url = (
                    "http://repo.openeuler.org/openEuler-"
                    + self.version.upper()
                    + "/docker_img/"
                    + arch
                    + "/openEuler-docker."
                    + arch
                    + ".tar.xz"
                )
                try:
                    wget.download(download_url)
                except Exception as err:
                    click.echo(click.style('[Prepare]' + err, fg="red"))
                    return pb.PUBLISH_FAILED
                click.echo(
                    "\n[Prepare] "
                    + "Download openEuler-docker."
                    + arch
                    + ".tar.xz successfully."
                )

            # 校验文件
            subprocess.call(
                ["rm", "-rf", "openEuler-docker." + arch + ".tar.xz.sha256sum"]
            )
            sha256sum_url = (
                "http://repo.openeuler.org/openEuler-"
                + self.version.upper()
                + "/docker_img/"
                + arch
                + "/openEuler-docker."
                + arch
                + ".tar.xz.sha256sum"
            )
            try:
                wget.download(sha256sum_url)
            except Exception as err:
                click.echo(click.style('\n[Prepare]' + err, fg="red"))
                return pb.PUBLISH_FAILED
            click.echo(
                "\n[Prepare] "
                + "Download openEuler-docker."
                + arch
                + ".tar.xz.sha256sum successfully."
            )
            subprocess.call([
                "shasum", "-c",
                "openEuler-docker." + arch + ".tar.xz.sha256sum"
            ])

            # 获得rootfs文件
            rootfs = "openEuler-docker-rootfs." + docker_arch + ".tar.xz"
            if os.path.exists(rootfs):
                continue
            tar_cmd = [
                "tar",
                "-xf",
                "openEuler-docker." + arch + ".tar.xz",
                "--exclude",
                "layer.tar",
            ]
            subprocess.call(tar_cmd)
            for file in os.listdir("."):
                if file.endswith(".tar") and not re.search("openEuler", file):
                    os.rename(file, "openEuler-docker-rootfs."
                              + docker_arch + ".tar")
                    subprocess.call([
                        "xz", "-z",
                        "openEuler-docker-rootfs." + docker_arch + ".tar"
                    ])
        click.echo("[Prepare] finished")
        return pb.PUBLISH_SUCCESS

    def build_and_push(self):
        os.chdir(CACHE_DATA_PATH)
        # 如果指定了自定义dockerfile，则使用其进行构建
        if os.path.exists(self.dockerfile):
            shutil.copy2(self.dockerfile, self.version + "/Dockerfile")

        # 检查是否安装qemu,以支持多平台构建
        if subprocess.call(["qemu-img", "--version"]) != 0:
            click.echo(click.style(
                    "\n[Prepare] please install qemu first, \
                    you can use command <yum install qemu-img>.",
                    fg="red"
            ))
            return pb.PUBLISH_FAILED
        # 登陆仓库
        username = os.environ["LOGIN_USERNAME"]
        password = os.environ["LOGIN_PASSWORD"]
        if (
            os.system(
                "echo %s | docker login --username %s --password-stdin %s"
                % (password, username, self.registry)
            )
            != 0
        ):
            return pb.PUBLISH_FAILED

        # 考虑到docker API for python版本的差异，直接调用buildx命令实现多平台镜像构建
        builder_name = "euler_builder_" + datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        if (
            subprocess.call(
                ["docker", "buildx", "create", "--use", "--name", builder_name]
            )
            != 0
        ):
            return pb.PUBLISH_FAILED
        # build并push docker image
        os.chdir(self.version)
        if (
            subprocess.call(
                [
                    "docker",
                    "buildx",
                    "build",
                    "--platform",
                    "linux/arm64,linux/amd64",
                    "-t",
                    self.repo + ":" + self.version,
                    "--push",
                    ".",
                ]
            )
            != 0
        ):
            return pb.PUBLISH_FAILED
        subprocess.call(["docker", "buildx", "stop", builder_name])
        subprocess.call(["docker", "buildx", "rm", builder_name])

        click.echo("[Push] finished")
        return pb.PUBLISH_SUCCESS

    # 对已构建的镜像进行测试，多平台镜像无法保存在本地，需要先从仓库pull后再执行测试过程
    def check(self):
        result = pb.PUBLISH_SUCCESS
        client = docker.from_env()
        image_tag = self.repo + ":" + self.version
        image = client.images(name=image_tag)
        if image == []:
            click.echo("Pulling " + image_tag + "...")
            client.pull(image_tag)

        # check basic information of new image
        image = client.images(name=image_tag)
        image_info = client.inspect_image(image[0]["Id"])
        for tag in image[0]["RepoTags"]:
            if tag == image_tag:
                # check OS type
                if image_info["Os"] != "linux":
                    click.echo(click.style(
                        "[Check] OS type <%s> is unknown." % image_info["Os"],
                        fg="red"
                    ))
                    result = pb.PUBLISH_FAILED
                # check platform type
                if image_info["Architecture"] != "amd64" and \
                   image_info["Architecture"] != "arm64":
                    click.echo(click.style(
                        "[Check] Architecture <%s> is not expected." %
                        image_info["Architecture"],
                        fg="red"
                    ))
                    result = pb.PUBLISH_FAILED

        # test time zone settings
        if _run(tag=image_tag, cmd="date", param="UTC") != pb.PUBLISH_SUCCESS:
            click.echo(click.style(
                "[Check] time zone setting is not UTC", fg="red"
            ))
            result = pb.PUBLISH_FAILED
        click.echo("[Check] finished")
        return result

    # 一键发布
    def publish(self):
        if self.prepare() != pb.PUBLISH_SUCCESS:
            click.echo(click.style(
                "[Publish] Download failed.", fg="red"
            ))
            return pb.PUBLISH_FAILED
        if self.build_and_push() != pb.PUBLISH_SUCCESS:
            click.echo(click.style(
                "[Publish] Build and push failed.", fg="red"
            ))
            return pb.PUBLISH_FAILED
        click.echo("[Publish] finished")
        return pb.PUBLISH_SUCCESS
