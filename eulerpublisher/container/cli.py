# coding=utf-8
import click

from eulerpublisher.container.container import ContainerPublisher


@click.group(name="container",
             help="Commands for publishing container images")
def group():
    pass


@group.command(name="prepare",
               help="Prepare original materials for building images")
@click.option(
    "-v", "--version", required=True,
    help="The version of container image, \
        such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
def prepare(version):
    obj = ContainerPublisher(version=version)
    obj.prepare()


@group.command(name="check",
               help="To test whether the built container image is correct")
@click.option(
    "-rp", "--repo", required=True,
    help="Your repository to push container image"
)
@click.option(
    "-v", "--version", required=True,
    help="The version of container image, \
        such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-rg", "--registry",
    default="registry-1.docker.io",
    help="Your registry to push container image, \
        the default is `registry-1.docker.io`. \
        you can use private registry such like `127.0.0.1:5000` or \
        other registry."
)
def check(repo, version, registry):
    obj = ContainerPublisher(repo=repo, version=version, registry=registry)
    obj.check()


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
    help="The version of container image, \
        such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-rg",
    "--registry",
    default="registry-1.docker.io",
    help="Your registry to push container image, \
        the default is `registry-1.docker.io`. \
        you can use private registry such like `127.0.0.1:5000` or \
        other registry."
)
@click.option(
    "-df",
    "--dockerfile",
    help="The dockerfile to define your image. \
        Please enter an absolute path of your dockerfile."
)
def push(repo, version, registry, dockerfile):
    obj = ContainerPublisher(
        repo=repo, version=version, registry=registry, dockerfile=dockerfile
    )
    obj.build_and_push()


@group.command(
    name="publish",
    help="To build and push container image to target repo"
)
@click.option(
    "-rp", "--repo", required=True,
    help="Your repository to push container image"
)
@click.option(
    "-v", "--version", required=True,
    help="The version of container image, \
        such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-rg",
    "--registry",
    default="registry-1.docker.io",
    help="Your registry to push container image, \
         the default is `registry-1.docker.io`. \
         you can use private registry such like `127.0.0.1:5000` or \
         other registry."
)
def publish(repo, version, registry):
    obj = ContainerPublisher(repo=repo, version=version, registry=registry)
    obj.publish()
