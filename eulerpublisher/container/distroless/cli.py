# coding=utf-8
import click
import sys


import eulerpublisher.publisher.publisher as pb
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
    help="The target repository to push distroless image to."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built distroless "
    "image. The default registry is `docker.io`"
    ", users can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.. While option `--multiPublish`"
    " is set, `--registry` is no longer needed.",
)
@click.option(
    "-a",
    "--arch",
    required=False,
    help="The architecture of required distroless image."
)
@click.option(
    "-f",
    "--dockerfile",
    required=False,
    help="The dockerfile to define your image. "
    "Please enter the path of your dockerfile "
    "if necessary, the default path is "
    "container/distroless/Dockerfile in the project.",
)
@click.option(
    "-n",
    "--name",
    required=True,
    help="The distroless container image name.",
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of the openEuler, "
    "such as 22.03-LTS, etc.",
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
    "config/container/app/registry.yaml. In this situation, the option "
    "`--registry` are no longer needed.",
)
@click.argument("packages", nargs=-1)
def build(repo, registry, arch, dockerfile, name, version, mpublish, packages):
    if mpublish:
        click.echo("`-g, --registry` option will not be used "
            "while `-m, --mpublish` is set.")
    obj = DistrolessPublisher(
        repo=repo,
        registry=registry,
        arch=arch,
        dockerfile=dockerfile,
        name=name,
        version=version.lower(),
        packages=packages,
        multi=mpublish
    )
    ret = obj.build()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(
    name="push",
    help="Push openEuler distroless image to target repository(s)"
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
    default="docker.io",
    help="The registry where to push the built distroless "
    "image. The default registry is `docker.io`"
    ", users can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.. While option `--multiPublish`"
    " is set, `--registry` is no longer needed.",
)
@click.option(
    "-a",
    "--arch",
    required=False,
    help="The architecture of required distroless image."
)
@click.option(
    "-n",
    "--name",
    required=True,
    help="The application container image name.",
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of the openEuler, such as 22.03-LTS, etc.",
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
    "config/container/app/registry.yaml. In this situation, the option "
    "`--registry` are no longer needed.",
)
def push(repo, registry, arch, name, version, mpublish):
    if mpublish:
        click.echo("`-g, --registry` option will not be used "
            "while `-m, --mpublish` is set.")
    obj = DistrolessPublisher(
        repo=repo,
        registry=registry,
        name=name,
        arch=arch,
        version=version.lower(),
        multi=mpublish
    )
    ret = obj.push()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)

@group.command(
    name="publish",
    help="Publish openEuler distroless image to target repository(s)"
)
@click.option(
    "-a",
    "--arch",
    help="The architecture of required distroless image, "
    "the default is multi-platform of arm64 and amd64."
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
    default="docker.io",
    help="The registry where to push the built distroless "
    "image. The default registry is `docker.io`"
    ", users can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.. While option `--multiPublish`"
    " is set, `--registry` is no longer needed.",
)
@click.option(
    "-f",
    "--dockerfile",
    required=False,
    help="The dockerfile to define your image. "
    "Please enter the path of your dockerfile "
    "if necessary, the default path is "
    "container/distroless/Dockerfile in the project.",
)
@click.option(
    "-n",
    "--name",
    required=True,
    help="The application container image name.",
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of the openEuler, such as 22.03-LTS, etc.",
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
    "config/container/app/registry.yaml. In this situation, the option "
    "`--registry` is no longer needed.",
)
@click.argument("packages", nargs=-1)
def publish(arch, repo, registry, dockerfile, name, version, mpublish, packages):
    if mpublish:
        click.echo("`-g, --registry` option will not be used "
            "while `-m, --mpublish` is set.")
    obj = DistrolessPublisher(
        arch=arch,
        repo=repo,
        registry=registry,
        packages=packages,
        dockerfile=dockerfile,
        name=name,
        version=version.lower(),
        multi=mpublish
    )
    if (not arch):
        if obj.build_and_push() != pb.PUBLISH_SUCCESS:
            sys.exit(1)
    else:
        if obj.build() != pb.PUBLISH_SUCCESS:
            sys.exit(1)
        if obj.push() != pb.PUBLISH_SUCCESS:
            sys.exit(1)
    sys.exit(0)
