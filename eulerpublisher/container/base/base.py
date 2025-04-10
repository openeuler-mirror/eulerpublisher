# coding=utf-8
import click
import os
import re
import requests
import shutil
import subprocess
import yaml


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH, OPENEULER_DOCKERFILE, logger
from eulerpublisher.publisher import OPENEULER_REPO

CACHE_DATA_PATH = "/tmp/eulerpublisher/container/base/"
DOCKERFILE_PATH = EP_PATH + "config/container/base/Dockerfile"
TAGS = EP_PATH + "config/container/base/tags.yaml"
DEFAULT_REGISTRY = EP_PATH + "config/container/base/registry.yaml"
TESTCASE_PATH = EP_PATH + "tests/container/base/openeuler_test.sh"


# tag image
def _get_tags(repository, version, multi):
    repo_list = []
    if not multi:
        repo_list.append(repository)
    else:
        with open(multi, "r") as f:
            env = yaml.safe_load(f)
        for key in env:
            repo_list.append(str(env[key][2]))
    # tag image for all registries
    tags = ""
    for repo in repo_list:
        tags += "-t " + repo + ":" + version.lower()
        with open(TAGS, "r") as f:
            data = yaml.safe_load(f)
        version = version.upper()
        if version in data:
            for tag in data[version]:
                tags += " -t " + repo + ":" + str(tag)
        tags += " "
    return tags

def _get_latest_version():
    with open(TAGS, "r") as f:
        data = yaml.safe_load(f)
    for item in data:
        for tag in data[item]:
            if str(tag).lower() == "latest":
                return item
    return ""

def _get_dockerfile():
    response = requests.get(OPENEULER_DOCKERFILE)
    if response.status_code == 200:
        with open(DOCKERFILE_PATH, "w") as f:
            f.write(response.text)
    else:
        raise Exception(
            "Failed to download the Dockerfile."
        )
    return DOCKERFILE_PATH

# Class for publishing openEuler container images
class OePublisher(pb.Publisher):
    def __init__(
        self, repo="", version="", registry="", index="", dockerfile="", multi=False
    ):
        self.repo = repo
        self.version = version
        self.registry = registry
        self.index = index
        # get Dockerfile path
        if dockerfile:
            self.dockerfile = os.path.abspath(dockerfile)
        else:
            self.dockerfile = _get_dockerfile()

        # get multiple-registry yaml path
        if multi:
            if (not "EP_LOGIN_FILE" in os.environ) or (not os.environ["EP_LOGIN_FILE"]):
                self.multi_file = DEFAULT_REGISTRY
            else:
                self.multi_file = os.path.abspath(os.environ["EP_LOGIN_FILE"])
        else:
            self.multi_file = ""

        # get all tags
        self.tags = _get_tags(
            repository=self.registry + "/" + self.repo,
            version=self.version,
            multi=self.multi_file,
        )

    def prepare(self):
        os.makedirs(CACHE_DATA_PATH, exist_ok=True)
        os.chdir(CACHE_DATA_PATH)
        os.makedirs(self.version, exist_ok=True)
        # shutil.copy2(self.dockerfile, self.version + "/Dockerfile")
        os.chdir(self.version)

        for arch in pb.ARCHS:
            if arch == "x86_64":
                docker_arch = "amd64"
            elif arch == "aarch64":
                docker_arch = "arm64"
            # download base images
            index = (
                "openEuler-"
                + self.version.upper()
                + "/"
                + self.index
                + "/"
                + arch
                + "/"
            )
            file_name = "openEuler-docker." + arch + ".tar.xz"
            if not os.path.exists(file_name):
                download_url = OPENEULER_REPO + index + file_name
                if pb.download(download_url) != pb.PUBLISH_SUCCESS:
                    return pb.PUBLISH_FAILED
                logger.info("\n[Prepare] Download %s successfully." % file_name)
            # check
            sha256sum = file_name + ".sha256sum"
            subprocess.call(["rm", "-rf", sha256sum])
            sha256sum_url = OPENEULER_REPO + index + sha256sum
            if pb.download(sha256sum_url) != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
            logger.info("\n[Prepare] Download %s successfully." % sha256sum)
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
                    os.rename(file, "openEuler-docker-rootfs." + docker_arch + ".tar")
                    subprocess.call(
                        ["xz", "-z", "openEuler-docker-rootfs." + docker_arch + ".tar"]
                    )
        logger.info("[Prepare] finished")
        return pb.PUBLISH_SUCCESS

    def build_and_push(self):
        try:
            os.chdir(CACHE_DATA_PATH)
            shutil.copy2(self.dockerfile, self.version + "/Dockerfile")

            # ensure qemu is installed so that it can build multi-platform images
            if pb.check_qemu() != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
            # ensure the docker is starting
            if pb.start_docker() != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
            # login registry
            if (
                pb.login_registry(registry=self.registry, multi=self.multi_file)
                != pb.PUBLISH_SUCCESS
            ):
                return pb.PUBLISH_FAILED
            # build multi-platform images with 'buildx'
            builder = pb.create_builder()
            # build and push docker image
            os.chdir(self.version)
            ret = subprocess.call(
                "docker buildx build "
                + "--platform linux/arm64,linux/amd64 "
                + self.tags
                + " --push "
                + ".",
                shell=True
            )
            subprocess.call(["docker", "buildx", "stop", builder])
            subprocess.call(["docker", "buildx", "rm", builder])
            if ret != 0:
                return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            logger.error(f"[Build and Push] {err}")
        logger.info("[Build and Push] finished")
        return pb.PUBLISH_SUCCESS

    # Run test script
    def check(self, tag="", script=""):
        try:
            if not script:
                script = TESTCASE_PATH
            if not os.path.exists(script):
                logger.error(f"[Check] test script `{script}` does not exist")
                return pb.PUBLISH_FAILED
            if tag == "latest":
                tag = _get_latest_version().lower()
            logger.info(f"[Check] checking openeuler:{tag} ...")
            env_vars = {'DOCKER_TAG': tag}
            os.chmod(script, 0o755)
            process = subprocess.Popen(
                script,
                shell=True,
                env={**os.environ, **env_vars}
            )
            if process.wait() != 0:
                logger.error(f"[Check] test failed")
                return pb.PUBLISH_FAILED
        except subprocess.CalledProcessError as err:
            logger.critical(f"[Check] {err}")
        logger.info("[Check] finished")
        return pb.PUBLISH_SUCCESS

    # Publish with one click
    def publish(self):
        logger.info("\n[Publish] start to publish openEuler-" + self.version.upper())
        if self.prepare() != pb.PUBLISH_SUCCESS:
            logger.error("[Publish] Download failed.")
            return pb.PUBLISH_FAILED
        if self.build_and_push() != pb.PUBLISH_SUCCESS:
            logger.error("[Publish] Build and push failed.")
            return pb.PUBLISH_FAILED
        if self.check(tag=self.version.lower()) != pb.PUBLISH_SUCCESS:
            logger.error("[Publish] Unit test failed.")
            return pb.PUBLISH_FAILED
        logger.info("[Publish] finished")
        return pb.PUBLISH_SUCCESS
