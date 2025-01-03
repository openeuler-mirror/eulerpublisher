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

# transform openEuler version into specifical format
# e.g., 22.03-lts-sp3 -> oe2203sp3
def transform_version_format(os_version: str):
    # check if os_version has substring "-sp"
    if "-sp" in os_version:
        # delete "lts" in os_version
        os_version = os_version.replace("lts", "")
    # delete all "." and "-"
    ret = os_version.replace(".", "").replace("-", "")
    return f"oe{ret}"

def init_dockerfile(param_dockerfile, default_dockerfile):
    # get Dockerfile path
    if param_dockerfile:
        dockerfile = os.path.abspath(param_dockerfile)
    else:
        dockerfile = default_dockerfile
    if os.path.exists(dockerfile):
        return os.path.abspath(dockerfile)
    return ""

def init_multi_file(multi):
    if multi:
        # if EP_LOGIN_FILE exists or valuable
        if (not "EP_LOGIN_FILE" in os.environ) or (not os.environ["EP_LOGIN_FILE"]):
            return DEFAULT_REGISTRY
        else:
            return os.path.abspath(os.environ["EP_LOGIN_FILE"])
    else:
        return ""

# architecture of required image, default is multi-platform
def init_platform(arch):
    if arch == "aarch64":
        return "linux/arm64"
    elif arch == "x86_64":
        return "linux/amd64"
    return "linux/amd64,linux/arm64"

# tag image for all registries
def init_tags(registry, repo, tag, multi):
    full_repos = []
    if not multi:
        full_repos.append(registry + '/' + repo)
    else:
        with open(multi, "r") as f:
            env = yaml.safe_load(f)
        for key in env:
            full_repos.append(str(key) + '/' + repo)
    tags_bulid = ""
    tags_push = []
    for item in full_repos:
        tags_bulid += "-t " + item + ":" + tag['tag']
        tags_bulid += " "
        if tag['latest']:
            tags_bulid += "-t " + item + ":latest"
            tags_bulid += " "
        tags_push.append(item + ":" + tag['tag'])
    return tags_bulid, tags_push

# workdir
def init_workdir(dockerfile):
    if (not "EP_APP_WORKDIR" in os.environ) or (not os.environ["EP_APP_WORKDIR"]):
        return os.path.dirname(dockerfile)
    return os.path.abspath(os.environ["EP_APP_WORKDIR"])

def build(op="load", param={}, build_args={}):
    arg_str = " ".join([
        f"--build-arg {key}={value}" for key, value in build_args.items()
    ])
    command = "docker buildx build --platform {} {} {} --{} .".format(
        param.platform, param.tags_build, arg_str, op
    )
    return build_command(command, param.workdir, param.dockerfile)

def build_command(command, workdir="", dockerfile=""):
    try:
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        os.chdir(workdir)
        if workdir != os.path.dirname(dockerfile):
            shutil.copy2(dockerfile, "./")
        # ensure qemu is installed
        if pb.check_qemu() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        # ensure the docker is starting
        if pb.start_docker() != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
        # build images with 'buildx'
        builder = pb.create_builder()
        ret = subprocess.call(command, shell=True)
        subprocess.call(["docker", "buildx", "stop", builder])
        subprocess.call(["docker", "buildx", "rm", builder])
        if ret != 0:
            return pb.PUBLISH_FAILED
    except (OSError, subprocess.CalledProcessError) as err:
        raise err
    click.echo("[Build] finished")
    return pb.PUBLISH_SUCCESS

def push(param={}):
    try:
        # login registry
        if (
            pb.login_registry(registry=param.registry, multi=param.multi_file)
            != pb.PUBLISH_SUCCESS
        ):
            return pb.PUBLISH_FAILED
        # push
        for tag in param.tags_push:
            if subprocess.call("docker push " + tag, shell=True) != 0:
                return pb.PUBLISH_FAILED
    except (OSError, subprocess.CalledProcessError) as err:
        click.echo(click.style(f"[Push] {err}", fg="red"))
    click.echo("[Push] finished")
    return pb.PUBLISH_SUCCESS

def build_and_push(param={}, build_args={}):
    try:
        # login registry
        if (
            pb.login_registry(registry=param.registry, multi=param.multi_file)
            != pb.PUBLISH_SUCCESS
        ):
            return pb.PUBLISH_FAILED
        if build(
            op="push", param=param, build_args=build_args
        ) != pb.PUBLISH_SUCCESS:
            return pb.PUBLISH_FAILED
    except (OSError, subprocess.CalledProcessError) as err:
        click.echo(click.style(f"[Push] {err}", fg="red"))
    click.echo("[Push] finished")
    return pb.PUBLISH_SUCCESS