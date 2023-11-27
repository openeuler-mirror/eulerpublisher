# coding=utf-8
import click
import sys
import os


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.container.container import ContainerPublisher


@click.group(name="container",
             help="Commands for publishing container images")
def group():
    pass


@group.command(name="prepare",
               help="Prepare original materials for building images")
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-i",
    "--index",
    required=False,
    default="docker_img",
    help="The link index of docker image you want to publish "\
        "from `repo.openeuler.org` to your registry, "\
        "such as `docker_img` or `docker_img/update/current`,"\
        " the default is `docker_img`."
)
def prepare(version, index):
    obj = ContainerPublisher(version=version, index=index)
    ret = obj.prepare()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    else:
        sys.exit(0)


@group.command(name="check",
               help="To test whether the built container image is correct")
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The repository where the tested image is pulled from."
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built container "\
         "image. The default registry is `docker.io`"\
         ", you can choose others such like `quay.io`,"\
         " `hub.oepkgs.net`, etc."
)
def check(repo, version, registry):
    obj = ContainerPublisher(repo=repo, version=version, registry=registry)
    ret = obj.check()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(name="push",
               help="To build and push container image to target repo")
@click.option(
    "-p",
    "--repo",
    required=True,
    help="The target repository to push container image to. "
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built container "\
         "image. The default registry is `docker.io`"\
         ", you can choose others such like `quay.io`,"\
         " `hub.oepkgs.net`, etc."
)
@click.option(
    "-f",
    "--dockerfile",
    default="",
    help="The dockerfile to define your image. "\
        "Please enter the path of your dockerfile "\
        "if necessary."
)
def push(repo, version, registry, dockerfile):
    obj = ContainerPublisher(
        repo=repo, 
        version=version,
        registry=registry,
        dockerfile=dockerfile
    )
    ret = obj.build_and_push()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)


@group.command(
    name="publish",
    help="To publish container image to target repo"
)
@click.option(
    "-p",
    "--repo",
    default="",
    help="The target repository to push container image to. "\
         "This option is required while option `--multiPublish`"\
         " is not set."
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-g",
    "--registry",
    default="docker.io",
    help="The registry where to push the built container "\
         "image. The default registry is `docker.io`"\
         ", you can choose others such like `quay.io`,"\
         " `hub.oepkgs.net`, etc.. While option `--multiPublish`"\
         " is set, `--registry` is no longer needed."
)
@click.option(
    "-f",
    "--dockerfile",
    default="",
    help="The dockerfile to define your image. "\
        "Please enter the path of your dockerfile "\
        "if necessary."
)
@click.option(
    "-i",
    "--index",
    required=False,
    default="docker_img",
    help="The link index of docker image you want to publish "\
        "from `repo.openeuler.org` to your registry, "\
        "such as `docker_img` or `docker_img/update/current`,"\
        " the default is `docker_img`."
)
@click.option(
    "-m",
    "--mpublish",
    is_flag=True,
    help="This option decides whether to publish the image to "\
        "multiple repositories. "\
        "While this option is set, all target repositories must "\
        "be provided in etc/container/registry.yaml, and the "\
        "options `--repo` and `--registry` are no longer needed."
)
def publish(repo, version, registry, dockerfile, index, mpublish):
    if mpublish:
        multi = True
    else:
        multi = False
    obj = ContainerPublisher(
        repo=repo,
        version=version,
        registry=registry,
        dockerfile=dockerfile,
        index=index,
        multi=multi
    )
    ret = obj.publish()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)
