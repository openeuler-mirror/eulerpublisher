# coding=utf-8
import click

from eulerpublisher.cloudimg.gen.gen import GenPublisher


@click.group(
    name="gen",
    help="Commands for building generic cloud images"
)
def group():
    pass


@group.command(
    name="prepare",
    help="Prepare original materials for building generic cloud image"
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of cloud image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-a",
    "--arch",
    required=True,
    help="The architecture of cloud image, "\
        "limited to `x86_64` or `aarch64`."
)
def prepare(version, arch):
    obj = GenPublisher(version=version, arch=arch)
    obj.prepare()


@group.command(name="build", help="Build generic cloud image.")
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of cloud image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-a",
    "--arch",
    required=True,
    help="The architecture of cloud image, "\
        "limited to `x86_64` or `aarch64`."
)
@click.option(
    "-p",
    "--rpmlist",
    help="The packages you want to install."
)
@click.option(
    "-o",
    "--output",
    help="The name of built cloud image."
)
def build(version, arch, rpmlist, output):
    obj = GenPublisher(version=version,
                       arch=arch,
                       rpmlist=rpmlist,
                       output=output)
    obj.prepare()
    obj.build()