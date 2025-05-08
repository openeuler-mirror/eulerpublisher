# coding=utf-8
import click
import sys
import eulerpublisher.publisher.publisher as pb
from eulerpublisher.publisher import logger
from eulerpublisher.container.distroless.distroless import DistrolessPublisher


@click.group(
    name="distroless",
    help="Command for publishing openeuler distroless container images"
)
def group():
    pass

@group.command(
    name="build",
    help="Build openEuler distroless image"
)
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The target repository to push distroless image onto."
)
@click.option(
    "-f",
    "--distrofile",
    required=True,
    help="The configuration file named `Distrofile` to define how to build your distroless images. "
)
@click.option(
    "-t",
    "--tag",
    default="latest",
    help="The distroless container image tag.",
)
def build(repo, distrofile, tag):
    obj = DistrolessPublisher(repo=repo, registry="docker.io", distrofile=distrofile, tag=tag)
    ret = obj.build()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(
    name="publish",
    help="Publish openEuler distroless image to target repository(s)"
)
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The target repository to push distroless image to."
)
@click.option(
    "-g",
    "--registry",
    type=str,
    help="The registry where to push the built distroless "
    "image. The default registry is `docker.io`"
    ", users can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.. While option `--multiPublish`"
    " is set, `--registry` is no longer needed.",
)
@click.option(
    "-f",
    "--distrofile",
    required=True,
    help="The configuration file named `Distrofile` to define how to build your distroless images. "
)
@click.option(
    "-t",
    "--tag",
    default="latest",
    help="The distroless container image tag.",
)
@click.option(
    "-m",
    "--mpublish",
    is_flag=True,
    help="This option decides whether to publish the image products to "
    "multiple repositories. While using this option, users may first "
    "provide the yaml file by `export EP_LOGIN_FILE=your_yaml_path`, "
    "which includes login information of all target repositories. "
    "The default target repositories are provided in "
    "config/container/distroless/registry.yaml."
)
def publish(repo, registry, distrofile, tag, mpublish):
    if mpublish and registry:
        logger.warning("`-g, --registry` option will not be used "
            "while `-m, --mpublish` is set.")
    if not registry:
        registry = "docker.io"
    obj = DistrolessPublisher(
        repo=repo,
        registry=registry,
        distrofile=distrofile,
        tag=tag,
        multi=mpublish
    )
    if obj.build_and_push() != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)
