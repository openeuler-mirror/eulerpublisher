# coding=utf-8
import click
import sys


import eulerpublisher.publisher.publisher as pb
from eulerpublisher.container.container import ContainerPublisher


@click.group(name="container",
             help="Commands for publishing container images")
def group():
    pass


@group.command(name="prepare",
               help="Prepare original materials for building images")
@click.option(
    "-v", "--version", required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-i", "--index", required=False,
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
    "-rp", "--repo", required=True,
    help="Your repository to check container image"
)
@click.option(
    "-v", "--version", required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-rg", "--registry",
    default="registry-1.docker.io",
    help="Your registry to push container image, "\
        "the default is `registry-1.docker.io`. "\
        "you can use private registry such like `127.0.0.1:5000` or "\
        "other registry."
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
    "-rp", "--repo", required=True,
    help="Your repository to push container image"
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-rg",
    "--registry",
    nargs=2,
    default=["registry-1.docker.io","https://index.docker.io/v1/"],
    help="The registry name and its url where to push container "\
         "image. The default registry is `registry-1.docker.io`"\
         " and its url is `https://index.docker.io/v1/`."
)
@click.option(
    "-df",
    "--dockerfile",
    help="The dockerfile to define your image. "\
        "Please enter an absolute path of your dockerfile."
)
def push(repo, version, registry, dockerfile):
    registry_name, registry_url = registry
    obj = ContainerPublisher(
        repo=repo, version=version,
        registry=registry_name, registry_url=registry_url,
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
    "-rp", "--repo", required=True,
    help="Your repository to push container image"
)
@click.option(
    "-v", "--version", required=True,
    help="The version of container image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-rg",
    "--registry",
    nargs=2,
    default=["registry-1.docker.io","https://index.docker.io/v1/"],
    help="The registry name and its url where to push container "\
         "image. The default registry is `registry-1.docker.io`"\
         " and its url is `https://index.docker.io/v1/`."
)
@click.option(
    "-df",
    "--dockerfile",
    help="The dockerfile to define your image. "\
        "Please enter an absolute path of your dockerfile."
)
@click.option(
    "-i", "--index", required=False,
    default="docker_img",
    help="The link index of docker image you want to publish "\
        "from `repo.openeuler.org` to your registry, "\
        "such as `docker_img` or `docker_img/update/current`,"\
        " the default is `docker_img`."
)
def publish(repo, version, registry, dockerfile, index):
    registry_name, registry_url = registry
    obj = ContainerPublisher(
        repo=repo, version=version, registry=registry_name,
        registry_url=registry_url, dockerfile=dockerfile, index=index)
    ret = obj.publish()
    if ret != pb.PUBLISH_SUCCESS:
        sys.exit(1)
    sys.exit(0)
