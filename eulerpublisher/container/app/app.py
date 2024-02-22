# coding=utf-8
import click
import os
import shutil
import subprocess
import yaml


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import EP_PATH


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
        tags_bulid += "-t " + item + ":" + tag
        tags_bulid += " "
        tags_push.append(item + ":" + tag)
    return tags_bulid, tags_push


class AppPublisher(pb.Publisher):
    def __init__(
        self, repo="", registry="", tag="", arch="", dockerfile="", multi=False
    ):
        self.repo = repo
        self.registry = registry
        self.dockerfile = os.path.abspath(dockerfile)
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
            if (
                subprocess.call(
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
                != 0
            ):
                return pb.PUBLISH_FAILED
            subprocess.call(["docker", "buildx", "stop", builder])
            subprocess.call(["docker", "buildx", "rm", builder])
        except (OSError, subprocess.CalledProcessError) as err:
            click.echo(click.style(f"[Build] {err}", fg="red"))
        click.echo("[Build] finished")
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
                if subprocess.call("docker push " + tag, shell=True)!= 0:
                    return pb.PUBLISH_FAILED
        except (OSError, subprocess.CalledProcessError) as err:
            click.echo(click.style(f"[Push] {err}", fg="red"))
        click.echo("[Push] finished")
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
            self.build(op="push")
        except (OSError, subprocess.CalledProcessError) as err:
            click.echo(click.style(f"[Push] {err}", fg="red"))
        click.echo("[Push] finished")
        return pb.PUBLISH_SUCCESS
    
    # Run test script
    def check(self, image_name="", tag="", script=""):
        try:
            if not script:
                script = TESTCASE_PATH + image_name + TESTCASE_SUFFIX
            if not os.path.exists(script):
                click.echo(click.style(
                    f"[Check] test script `{script}` does not exist", fg="red"
                ))
                return pb.PUBLISH_FAILED
            click.echo(click.style(f"[Check] checking {image_name}:{tag} ..."))
            env_vars = {'DOCKER_TAG': tag}
            os.chmod(script, 0o755)
            process = subprocess.Popen(
                script,
                shell=True,
                env={**os.environ, **env_vars}
            )
            if process.wait() != 0:
                click.echo(click.style(f"[Check] test failed", fg="red"))
                return pb.PUBLISH_FAILED
        except subprocess.CalledProcessError as err:
            click.echo(click.style(f"[Check] {err}", fg="red"))
        click.echo("[Check] finished")
        return pb.PUBLISH_SUCCESS