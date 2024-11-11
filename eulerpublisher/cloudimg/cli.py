# coding=utf-8
import click

from eulerpublisher.cloudimg.cloudimg import CloudimgPublisher

@click.group(name="cloudimg", help="Command for publishing cloud images")
def group():
    pass

@group.command(
    name="prepare", help="Prepare original materials for building generic cloud image"
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of cloud image, " "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-a",
    "--arch",
    required=True,
    help="The architecture of cloud image, " "limited to `x86_64` or `aarch64`."
)
def prepare(version, arch):
    obj = CloudimgPublisher(version=version, arch=arch)
    obj.prepare()


@group.command(name="build", help="Build cloud image.")
@click.option(
    "-t",
    "--target",
    required=True,
    help="The target cloud provider, " "limited to `huawei`, `alibaba`, or `tencent`."
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of cloud image, " "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-a",
    "--arch",
    required=True,
    help="The architecture of cloud image, " "limited to `x86_64` or `aarch64`."
)
@click.option("-p", "--rpmlist", help="The packages you want to install.")
def build(target, version, arch, rpmlist):
    obj = CloudimgPublisher(target=target, version=version, arch=arch, rpmlist=rpmlist)
    obj.build()

@group.command(name="push", help="Push generic cloud image to cloud provider.")
@click.option(
    "-t",
    "--target",
    required=True,
    help="The target cloud provider, " "limited to `huawei`, `alibaba`, or `tencent`."
)
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of cloud image, " "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-a",
    "--arch",
    required=True,
    help="The architecture of cloud image, " "limited to `x86_64` or `aarch64`."
)
@click.option(
    "-b",
    "--bucket",
    required=True,
    help="The bucket on target cloud provider."
)
@click.option(
    "-r",
    "--region",
    required=True,
    help="The region on target cloud provider, " "such as `cn-north-1`, `ap-shenzhen`, etc."
)
@click.option(
    "-f",
    "--file",
    required=True,
    help="The image file."
)
def push(target, version, arch, bucket, region, file):
    obj = CloudimgPublisher(target=target, version=version, arch=arch, bucket=bucket, region=region, image=file)
    obj.push()
