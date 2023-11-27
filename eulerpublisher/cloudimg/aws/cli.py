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
def prepare(version, arch, bucket):
    obj = AwsPublisher(version=version,
                       arch=arch,
                       bucket=bucket)
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
    obj = AwsPublisher(version=version,
                       arch=arch,
                       rpmlist=rpmlist,
                       bucket=bucket,
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
def publish(version, arch, rpmlist, bucket, region):
    obj = AwsPublisher(version=version,
                       arch=arch,
                       rpmlist=rpmlist,
                       bucket=bucket,
                       region=region)
    obj.prepare()
    obj.build()