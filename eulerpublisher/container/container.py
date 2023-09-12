# coding=utf-8
import click
import datetime
import docker
import os
import platform
import re
import shutil
import subprocess
import wget
import yaml
import time


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH
from eulerpublisher.publisher import OPENEULER_REPO

CACHE_DATA_PATH = "/tmp/eulerpublisher/container/"
DOCKERFILE_PATH = EP_PATH + "container/Dockerfile"
TAGS = EP_PATH + "container/tags.yaml"

# max time(sencond) to start docker
START_TIMEOUT = 300
# times to retry download
RETRY_DOWNLOAD = 10


def _get_tags(registry, repo, key):
    tags = "-t " + registry + "/" + repo + ":" + key.lower()
    with open(TAGS, 'r') as f:
        data = yaml.safe_load(f)
    key = key.upper()
    if key in data:
        for tag in data[key]:
            tags += " -t " + registry + "/" + repo + ":" + str(tag)
    return tags


# Run container and compare the result with 'param'
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


# Start docker
def _start_docker():
    cnt = 0
    if subprocess.call(['docker', 'info'], stdout = subprocess.PIPE, \
            stderr = subprocess.STDOUT):
        syst = platform.system()
        if syst == "Darwin":
            subprocess.call(['open', '-g', '-a', 'Docker'], \
                stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        elif syst == "Linux":
            subprocess.call(['systemctl', 'start', 'docker'], \
                stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        else:
            click.echo(click.style('\nUnsupported system %s.' \
                % syst, fg="red"))
        click.echo('Starting docker ...')
    while subprocess.call(['docker', 'info'], stdout = subprocess.PIPE, \
            stderr = subprocess.STDOUT):
        if cnt >= START_TIMEOUT:
            click.echo(click.style('\nFailed to start docker, ' \
                'please ensure the docker is installed.', fg="red"))
            return pb.PUBLISH_FAILED
        time.sleep(5)
        cnt += 5
    return pb.PUBLISH_SUCCESS


def _download(url):
    retry_cnt = 0
    while retry_cnt < RETRY_DOWNLOAD:
        try:
            wget.download(url)
            return pb.PUBLISH_SUCCESS
        except Exception as err:
            click.echo(click.style(f"\nTry {retry_cnt+1}/{RETRY_DOWNLOAD}"\
                " failure: " + str(err), fg="red"))
            retry_cnt += 1
    return pb.PUBLISH_FAILED


# Class for publishing container images
class ContainerPublisher(pb.Publisher):
    def __init__(self,
                 repo=None,
                 version=None,
                 registry=None,
                 registry_url=None,
                 index=None,
                 dockerfile=None):
        self.repo = repo
        self.version = version
        self.registry = registry
        self.registry_url = registry_url
        self.dockerfile = dockerfile
        self.index = index
        if not self.dockerfile:
            self.dockerfile = ""

    def prepare(self):
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
            # download base images
            index = "openEuler-" + self.version.upper() + "/" + \
                self.index + "/" + arch + "/"
            file_name = "openEuler-docker." + arch + ".tar.xz"
            if not os.path.exists(file_name): 
                download_url = OPENEULER_REPO + index + file_name
                if _download(download_url) != pb.PUBLISH_SUCCESS:
                    return pb.PUBLISH_FAILED
                click.echo(
                    "\n[Prepare] Download %s successfully." % file_name
                )
            # check
            sha256sum = file_name + ".sha256sum"
            subprocess.call(["rm", "-rf", sha256sum])
            sha256sum_url = OPENEULER_REPO + index + sha256sum
            if _download(sha256sum_url) != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
            click.echo("\n[Prepare] Download %s successfully." % sha256sum)
            subprocess.call(["shasum", "-c", sha256sum])
            # get rootfs
            rootfs = "openEuler-docker-rootfs." + docker_arch + ".tar.xz"
            if os.path.exists(rootfs):
                continue
            tar_cmd = [
                "tar",
                "-xf",
                file_name,
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
        # to build with Dockerfile
        if os.path.exists(self.dockerfile):
            shutil.copy2(self.dockerfile, self.version + "/Dockerfile")
        # ensure that qemu is installed so that it can build multi-platform images
        if subprocess.call(["qemu-img", "--version"], \
                stdout = subprocess.PIPE,stderr = subprocess.STDOUT) != 0:
            click.echo(click.style(
                    "\n[Prepare] please install qemu first, \
                    you can use command <yum install qemu-img>.",
                    fg="red"
            ))
            return pb.PUBLISH_FAILED
        # ensure the docker is starting
        if _start_docker() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        # login registry
        username = os.environ["LOGIN_USERNAME"]
        password = os.environ["LOGIN_PASSWORD"]
        if subprocess.call("echo %s | docker login --username %s --password-stdin %s"
                % (password, username, self.registry_url), shell=True) != 0:
            return pb.PUBLISH_FAILED
        # to build mutil-platform images with 'buildx'
        builder_name = "euler_builder_" + datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        if subprocess.call([
            "docker", "buildx", "create", "--use", "--name", builder_name
        ],) != 0:
            return pb.PUBLISH_FAILED
        # build and push docker image
        os.chdir(self.version)
        if subprocess.call(
            "docker buildx build " + \
            "--platform linux/arm64,linux/amd64 " + \
            _get_tags(self.registry, self.repo, self.version) + \
            " --push " + \
            ".",
            shell=True
        )!= 0:
            return pb.PUBLISH_FAILED
        subprocess.call(["docker", "buildx", "stop", builder_name])
        subprocess.call(["docker", "buildx", "rm", builder_name])

        click.echo("[Push] finished")
        return pb.PUBLISH_SUCCESS

    # To test the new image，you should first pull it
    def check(self):
        result = pb.PUBLISH_SUCCESS
        client = docker.from_env()
        image_tag = self.registry + "/" + self.repo + ":" + self.version
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

    # Publish with one click
    def publish(self):
        click.echo("\n[Publish] start to publish openEuler-" + self.version + '...')
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
