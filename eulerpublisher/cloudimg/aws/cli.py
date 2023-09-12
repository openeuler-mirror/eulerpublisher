# coding=utf-8
import click

from eulerpublisher.cloudimg.aws.aws import AwsPublisher


@click.group(name="aws", help="Commands for publishing AMI")
def group():
    pass


@group.command(name="prepare",
               help="Prepare original materials for building AMI")
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
    "-b",
    "--bucket",
    required=True,
    help="The bucket_name identifier."
)
@click.option(
    "-i",
    "--index",
    default="virtual_machine_img",
    help="The link index of cloud image you want to build "\
        "based on. You can choose `virtual_machine_img`, "\
        "`virtual_machine_img/update/YYYY-MM-DD` or "\
        "`virtual_machine_img/update/current`, the default is "\
        "`virtual_machine_img`."
)
def prepare(version, arch, bucket, index):
    obj = AwsPublisher(version=version, arch=arch,
                       bucket=bucket, index=index)
    obj.prepare()


@group.command(name="build", help="Build AMI for AWS.")
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
    "-b",
    "--bucket",
    required=True,
    help="The bucket_name identifier."
)
@click.option(
    "-r",
    "--region",
    required=True,
    help="The AWS region, such as `ap-northeast-2`."
)
def build(version, arch, rpmlist, bucket, region):
    obj = AwsPublisher(version=version, arch=arch,
                       rpmlist=rpmlist, bucket=bucket,
                       region=region)
    obj.build()


@group.command(name="publish", help="Make AMI for AWS.")
@click.option(
    "-v",
    "--version",
    required=True,
    help="The version of cloud image, "\
        "such as 22.03-LTS, 22.03-LTS-SP1, etc."
)
@click.option(
    "-i",
    "--index",
    default="virtual_machine_img",
    help="The link index of cloud image you want to build "\
        "based on. You can choose `virtual_machine_img`, "\
        "`virtual_machine_img/update/YYYY-MM-DD` or "\
        "`virtual_machine_img/update/current`, the default is "\
        "`virtual_machine_img`."
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
    "-b",
    "--bucket",
    required=True,
    help="The bucket_name identifier."
)
@click.option(
    "-r",
    "--region",
    required=True,
    help="The AWS region, such as `ap-northeast-2`."
)
def publish(version, index, arch, rpmlist, bucket, region):
    obj = AwsPublisher(version=version, index=index,
                       arch=arch,
                       rpmlist=rpmlist, bucket=bucket,
                       region=region)
    obj.build()