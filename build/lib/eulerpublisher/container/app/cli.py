# coding=utf-8
import click
import sys
import warnings


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.container.app.app import AppPublisher


@click.group(
    name="app",
    help="Command for publishing openeuler application container images"
)
def group():
    pass


@group.command(
    name="build",
    help="Build openEuler application image"
)
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The target repository to push application image to."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built application "
    "image. The default registry is `docker.io`"
    ", users can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.. While option `--multiPublish`"
    " is set, `--registry` is no longer needed.",
)
@click.option(
    "-a",
    "--arch",
    required=True,
    help="The architecture of required application image."
)
@click.option(
    "-f",
    "--dockerfile",
    required=True,
    help="The dockerfile to define application image, "
    "users must enter the path of dockerfile.",
)
@click.option(
    "-t",
    "--tag",
    required=True,
    help="The application container image tag, it usually consists of "
    "SDK, application framework, and/or LLM information.",
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
def build(repo, registry, arch, dockerfile, tag, mpublish):
    if mpublish:
        click.echo("`-g, --registry` option will not be used "
            "while `-m, --mpublish` is set.")
    obj = AppPublisher(
        repo=repo,
        registry=registry,
        arch=arch,
        dockerfile=dockerfile,
        tag=tag,
        multi=mpublish,
    )
    ret = obj.build()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(
    name="push",
    help="Push openEuler application image to target repository(s)"
)
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The target repository to push application image to."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built application "
    "image. The default registry is `docker.io`"
    ", users can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.. While option `--multiPublish`"
    " is set, `--registry` is no longer needed.",
)
@click.option(
    "-t",
    "--tag",
    required=True,
    help="Tag of the application container image needs to push",
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
def push(repo, registry, tag, mpublish):
    if mpublish:
        click.echo("`-g, --registry` option will not be used "
            "while `-m, --mpublish` is set.")
    obj = AppPublisher(repo=repo, registry=registry, tag=tag, multi=mpublish)
    ret = obj.push()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)
    

@group.command(
    name="check",
    help="Check whether the image is as expected"
)
@click.option(
    "-n",
    "--name",
    help="The name of tested image.",
)
@click.option(
    "-h",
    "--hubnamespace",
    default="openeuler",
    help="The namespace of hub where the tested image stores, the default is `openeuler`.",
)
@click.option(
    "-s",
    "--script",
    help="The shell script for testing application container image.",
)
@click.option(
    "-t",
    "--tag",
    required=True,
    help="The tag of application container image, "
        "such as httpd2.4.51-oe2203lts, etc.",
)
def check(name, hubnamespace, script, tag):
    obj = AppPublisher()
    ret = obj.check(
        image_name=name,
        namespace=hubnamespace,
        script=script, tag=str(tag).lower()
    )
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(
    name="publish",
    help="Publish openEuler application image to target repository(s)"
)
@click.option(
    "-a",
    "--arch",
    help="The architecture of required application image, "
    "the default is multi-platform of arm64 and amd64."
)
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The target repository to push application image to."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built application "
    "image. The default registry is `docker.io`"
    ", users can choose others such like `quay.io`,"
    " `hub.oepkgs.net`, etc.. While option `--multiPublish`"
    " is set, `--registry` is no longer needed.",
)
@click.option(
    "-f",
    "--dockerfile",
    required=True,
    help="The dockerfile to define application image, "
    "users must enter the path of dockerfile.",
)
@click.option(
    "-t",
    "--tag",
    required=True,
    help="The application container image tag, it usually consists of "
    "SDK, application framework, and/or LLM information.",
)
@click.option(
    "-l",
    "--latest",
    type=bool,
    default=False,
    help="To show whether the tag is latest, and the image "
    "will be taged with both `tag` and `latest` while True."
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
def publish(arch, repo, registry, dockerfile, tag, latest, mpublish):
    if mpublish:
        click.echo("`-g, --registry` option will not be used "
            "while `-m, --mpublish` is set.")
    obj = AppPublisher(
        arch=arch,
        repo=repo,
        registry=registry,
        dockerfile=dockerfile,
        tag={'tag': tag, 'latest': latest},
        multi=mpublish,
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
