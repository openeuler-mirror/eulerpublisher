# coding=utf-8
import click
import sys


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.container.base.base import OePublisher


@click.group(
    name="base",
    help="Command for publishing openeuler base images"
)
def group():
    pass


@group.command(
    name="prepare",
    help="Prepare original materials for building images"
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, "
        "such as 22.03-LTS, 22.03-LTS-SP1, etc.",
)
@click.option(
    "-i",
    "--index",
    required=False,
    default="docker_img",
    help="The link index of docker image you want to publish "
    "from `repo.openeuler.org` to your registry, "
    "such as `docker_img` or `docker_img/update/current`,"
    " the default is `docker_img`.",
)
def prepare(version, index):
    obj = OePublisher(version=version, index=index)
    ret = obj.prepare()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    else:
        sys.exit(0)


@group.command(
    name="check",
    help="Check whether the image is as expected"
)
@click.option(
    "-s",
    "--script",
    help="The shell script for testing base container images.",
)
@click.option(
    "-t",
    "--tag",
    required=True,
    help="The tag of base container image, "
        "such as 22.03-LTS, 22.03-LTS-SP1, etc.",
)
def check(script, tag):
    obj = OePublisher()
    ret = obj.check(script=script, tag=str(tag).lower())
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(
    name="push",
    help="Build and push openEuler base image to target repository"
)
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The target repository to push container image to.",
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, "
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built container "
    "image. The default registry is `docker.io`"
    ", you can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.",
)
@click.option(
    "-f",
    "--dockerfile",
    default="",
    help="The dockerfile to define your image. "
    "Please enter the path of your dockerfile "
    "if necessary.",
)
def push(repo, version, registry, dockerfile):
    obj = OePublisher(
        repo=repo, version=version, registry=registry, dockerfile=dockerfile
    )
    ret = obj.build_and_push()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(
    name="publish",
    help="Publish openEuler base image to target repository(s)"
)
@click.option(
    "-p",
    "--repo",
    default="",
    help="The target repository to push container image to. "
    "This option is required while option `--mpublish`"
    " is not set.",
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, " 
        "such as 22.03-LTS, 22.03-LTS-SP1, etc.",
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built container "
    "image. The default registry is `docker.io`, "
    "you can choose others such like `quay.io`, "
    "`hub.oepkgs.net`, etc.. While option `--mpublish` "
    "is set, `--registry` is no longer needed.",
)
@click.option(
    "-f",
    "--dockerfile",
    default="",
    help="The dockerfile to define your image. "
    "Please enter the path of your dockerfile "
    "if necessary.",
)
@click.option(
    "-i",
    "--index",
    required=False,
    default="docker_img",
    help="The link index of docker image you want to publish "
    "from `repo.openeuler.org` to your registry, "
    "such as `docker_img` or `docker_img/update/current`,"
    " the default is `docker_img`.",
)
@click.option(
    "-m",
    "--mpublish",
    is_flag=True,
    help="This option decides whether to publish the image product to "
    "multiple repositories. While using this option, users may first "
    "provide the yaml file by `export EP_LOGIN_FILE=your_yaml_path`, "
    "which includes login information of all target repositories. "
    "The default target repositories are provided in "
    "etc/container/base/registry.yaml. In this situation,the options "
    "`--repo` and `--registry` are no longer needed.",
)
def publish(repo, version, registry, dockerfile, index, mpublish):
    if (not mpublish) and (not repo):
        raise TypeError("[Publish] `--repo` option is required.")
    obj = OePublisher(
        repo=repo,
        version=version,
        registry=registry,
        dockerfile=dockerfile,
        index=index,
        multi=mpublish,
    )
    ret = obj.publish()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)
