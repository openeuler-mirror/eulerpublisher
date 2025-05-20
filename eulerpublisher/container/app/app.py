# coding=utf-8
import click
import os
import shutil
import subprocess
import yaml


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH, logger


DEFAULT_REGISTRY = EP_PATH + "config/container/app/registry.yaml"
TESTCASE_PATH = EP_PATH + "tests/container/app/"
TESTCASE_SUFFIX = "_test.sh"


def _get_tags(registry, repo, tag, multi):
    full_repos = []
    if not multi:
        full_repos.append(registry + '/' + repo)
    else:
        with open(multi, "r") as f:
            env = yaml.safe_load(f)
        for key in env:
            full_repos.append(str(key) + '/' + repo)
    # tag image for all registries
    tags_bulid = ""
    tags_push = []
    
    for item in full_repos:
        tags_bulid += "-t " + item + ":" + tag['tag']
        tags_bulid += " "
        tags_push.append(item + ":" + tag['tag'])
        if tag['latest']:
            tags_bulid += "-t " + item + ":latest"
            tags_bulid += " "
            tags_push.append(item + ":latest")  
    return tags_bulid, tags_push

def _sync_images(source: str, targets=[]):
    try:
        for dest in targets:
            if subprocess.call(
                "regctl image copy " + \
                source + \
                " " + \
                dest, 
                shell=True
            ) != 0:
                return pb.PUBLISH_FAILED
    except (OSError, subprocess.CalledProcessError) as err:
        logger.error(f"Failed to sync images: {err}")
    logger.info("Sync images finished")       
    return pb.PUBLISH_SUCCESS    


class AppPublisher(pb.Publisher):
    def __init__(
        self, repo="", registry="", tag={'tag':"",'latest': False}, arch="", dockerfile="", multi=False
    ):
        self.repo = repo
        self.registry = registry
        if os.path.exists(dockerfile):
            self.dockerfile = os.path.abspath(dockerfile)
        else:
            self.dockerfile = ""
        # get multiple-registry yaml path
        if multi:
            # if EP_LOGIN_FILE exists or valuable
            if (not "EP_LOGIN_FILE" in os.environ) or (not os.environ["EP_LOGIN_FILE"]):
                self.multi_file = DEFAULT_REGISTRY
            else:
                self.multi_file = os.path.abspath(os.environ["EP_LOGIN_FILE"])
        else:
            self.multi_file = ""

        self.tags_build, self.tags_push = _get_tags(
            registry=registry, repo=repo, tag=tag, multi=self.multi_file
        )

        # architecture of required image, default is multi-platform
        if arch == "aarch64":
            self.platform = "linux/arm64"
        elif arch == "x86_64":
            self.platform = "linux/amd64"
        else:
            self.platform = "linux/amd64,linux/arm64"
        # workdir
        if (not "EP_APP_WORKDIR" in os.environ) or (not os.environ["EP_APP_WORKDIR"]):
            self.workdir = os.path.dirname(self.dockerfile)
        else:
            self.workdir = os.path.abspath(os.environ["EP_APP_WORKDIR"])

    def build(self, op="load"):
        try:
            if not os.path.exists(self.workdir):
                os.makedirs(self.workdir)
            os.chdir(self.workdir)
            if self.workdir != os.path.dirname(self.dockerfile):
                shutil.copy2(self.dockerfile, "./")
            # ensure qemu is installed
            if pb.check_qemu() != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
            # ensure the docker is starting
            if pb.start_docker() != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
            # build images with 'buildx'
            builder = pb.create_builder()
            ret = subprocess.call(
                "docker buildx build "
                + "--platform "
                + self.platform
                + " "
                + self.tags_build
                + " --"
                + op
                + " .",
                shell=True,
            )
            subprocess.call(["docker", "buildx", "stop", builder])
            subprocess.call(["docker", "buildx", "rm", builder])
            if ret != 0:
                return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            raise err
        logger.info("[Build] finished")
        return pb.PUBLISH_SUCCESS

    def push(self):
        try:
            # login registry
            if (
                pb.login_registry(registry=self.registry, multi=self.multi_file)
                != pb.PUBLISH_SUCCESS
            ):
                return pb.PUBLISH_FAILED
            # push
            for tag in self.tags_push:
                if subprocess.call("docker push " + tag, shell=True) != 0:
                    return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            logger.error(f"[Push] {err}")
        logger.info("[Push] finished")
        return pb.PUBLISH_SUCCESS
    
    # this function is only used for publishing multi-platform image
    def build_and_push(self):
        try:
            # login registry
            if (
                pb.login_registry(registry=self.registry, multi=self.multi_file)
                != pb.PUBLISH_SUCCESS
            ):
                return pb.PUBLISH_FAILED
            if self.build(op="push") != pb.PUBLISH_SUCCESS:
                return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            logger.error(f"[Push] {err}")
        logger.info("[Push] finished")
        return pb.PUBLISH_SUCCESS
    
    # Run test script
    def check(self, namespace="openeuler", image_name="", tag="", script=""):
        try:
            if not script:
                script = TESTCASE_PATH + image_name + TESTCASE_SUFFIX
            if not os.path.exists(script):
                logger.warning(f"[Check] File: {script} does not exist, no test runs.")
                return pb.PUBLISH_SUCCESS
            logger.info(f"[Check] checking {namespace}/{image_name}:{tag} ...")
            env_vars = {
                'DOCKER_TAG': tag,
                'DOCKER_NAMESPACE': namespace
            }
            os.chmod(script, 0o755)
            process = subprocess.Popen(
                script,
                shell=True,
                env={**os.environ, **env_vars}
            )
            if process.wait() != 0:
                logger.critical(f"[Check] test failed")
                return pb.PUBLISH_FAILED
        except subprocess.CalledProcessError as err:
            logger.error(f"[Check] {err}")
        logger.info("[Check] All tests are finished.")
        return pb.PUBLISH_SUCCESS
    
    def copy_and_push(self, source: str):
        '''
            This function has two steps:
            1. use multiple single images to create one multi-arch image on the source resgitry
            2. use `regctl image copy` to sync the multi-arch image on the source resgitry to other registries
        '''
        if not source:
            return pb.PUBLISH_FAILED
        # get the source registry, the default is `docker.io`
        src_tags = source.split()
        src_registry = src_tags[0].split("/", 1)[0]
        default_tags = [tag for tag in self.tags_push if tag.startswith(src_registry)]
        other_tags = [tag for tag in self.tags_push if not tag.startswith(src_registry)]
        
        # login registry
        if (pb.login_registry(registry=self.registry, multi=self.multi_file) != pb.PUBLISH_SUCCESS):
            return pb.PUBLISH_FAILED
        
        # use `buildx imagetools create` to create
        # a multi-arch image from multiple single-arch images
        try:
            if subprocess.call(
                "docker buildx imagetools create " + \
                " ".join([f"-t {tag}" for tag in default_tags]) + \
                " " + \
                " ".join([f"{tag}" for tag in src_tags]), 
                shell=True
            ) != 0:
                return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            logger.error(f"Failed to create image: {err}")
            
        # sync multi-arch image to all other registries
        if _sync_images(default_tags[0], other_tags) != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        logger.info("Sync images finished")
        return pb.PUBLISH_SUCCESS