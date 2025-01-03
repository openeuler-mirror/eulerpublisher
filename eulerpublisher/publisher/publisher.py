# coding=utf-8
import click
import datetime
import os
import platform
import subprocess
import wget
import time
import yaml


# global variables
PUBLISH_FAILED = 1
PUBLISH_SUCCESS = 0
ARCHS = ["x86_64", "aarch64"]

# max time(second) to start docker
START_TIMEOUT = 300
# times to retry download
RETRY_DOWNLOAD = 10


# Start docker
def start_docker():
    cnt = 0
    if subprocess.call(
        ["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ):
        syst = platform.system()
        if syst == "Darwin":
            subprocess.call(
                ["open", "-g", "-a", "Docker"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        elif syst == "Linux":
            subprocess.call(
                ["systemctl", "start", "docker"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        else:
            click.echo(click.style("\nUnsupported system %s." % syst, fg="red"))
        click.echo("Starting docker ...")
    while subprocess.call(
        ["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ):
        if cnt >= START_TIMEOUT:
            click.echo(
                click.style(
                    "\nFailed to start docker, "
                    "please restart docker manually.",
                    fg="red",
                )
            )
            return PUBLISH_FAILED
        time.sleep(5)
        cnt += 5
    return PUBLISH_SUCCESS


def download(url):
    retry_cnt = 0
    while retry_cnt < RETRY_DOWNLOAD:
        try:
            wget.download(url)
            return PUBLISH_SUCCESS
        except Exception as err:
            click.echo(
                click.style(
                    f"\nTry {retry_cnt+1}/{RETRY_DOWNLOAD}" " failure: " + str(err),
                    fg="red",
                )
            )
            time.sleep(5)
            retry_cnt += 1
    return PUBLISH_FAILED


def check_qemu():
    if (
        subprocess.call(
            ["qemu-img", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        != 0
    ):
        click.echo(
            click.style(
                "\n[Prepare] please install qemu first, \
            you can use command `yum install qemu-img>`.",
                fg="red",
            )
        )
        return PUBLISH_FAILED
    return PUBLISH_SUCCESS
    
def check_slim():
    if (
        subprocess.call(
            ["slim", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        != 0
    ):
        click.echo(
            click.style(
                "\n[Prepare] please install slim first, \
            you can use command `curl -sL https://raw.githubusercontent.com/slimtoolkit/slim/master/scripts/install-slim.sh | sudo -E bash - `.",
                fg="red",
            )
        )
        return PUBLISH_FAILED
    return PUBLISH_SUCCESS


def create_builder():
    builder = "euler_builder_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if subprocess.call([
        "docker", "buildx", "create",
        "--use", "--name", builder
    ]) != 0:
        return ""
    return builder


# login
def login_registry(registry, multi):
    # login single registry
    if not multi:
        if (
            subprocess.call(
                "echo %s | docker login --username %s "
                "--password-stdin %s"
                % (
                    os.environ["LOGIN_PASSWORD"],
                    os.environ["LOGIN_USERNAME"],
                    registry,
                ),
                shell=True,
            )
            != 0
        ):
            return PUBLISH_FAILED
        return PUBLISH_SUCCESS
    # login multiple registries in registry.yaml
    with open(multi, "r") as f:
        env = yaml.safe_load(f)

    """
    1. Login all target registries.
    2. Before logging in, all users and their passwords must
        be set into the environment
    """
    for key in env:
        username = os.environ[str(env[key][0])]
        password = os.environ[str(env[key][1])]
        if (
            subprocess.call(
                "echo %s | docker login --username %s "
                "--password-stdin %s" % (password, username, str(key)),
                shell=True,
            )
            != 0
        ):
            return PUBLISH_FAILED
    return PUBLISH_SUCCESS


# parent `publisher`
class Publisher:
    def __init__():
        pass

    # prepare stage
    def prepare():
        pass

    # `build` method that can be executed separately
    def build():
        pass

    # `push` method that can be executed separately
    def push():
        pass

    # The situation where `build` and `push` must be
    # executed at the same time
    def build_and_push():
        pass

    # One-click publishing
    def publish():
        pass
