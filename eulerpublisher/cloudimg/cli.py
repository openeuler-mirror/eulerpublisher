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
    "-c",
    "--config",
    required=True,
    help="Path to the YAML configuration file."
)
def prepare(config):
    obj = CloudimgPublisher(config_file=config)
    obj.prepare()


@group.command(name="build", help="Build cloud image.")
@click.option(
    "-c",
    "--config",
    required=True,
    help="Path to the YAML configuration file."
)
@click.option(
    "-t",
    "--target",
    required=True,
    help="The target cloud provider, "
    "limited to `huawei`, `alibaba`, `tencent`, `aws` or `azure`."
)
def build(config, target):
    obj = CloudimgPublisher(config_file=config, target=target)
    obj.build()


@group.command(name="push", help="Push generic cloud image to cloud provider.")
@click.option(
    "-c",
    "--config",
    required=True,
    help="Path to the YAML configuration file."
)
@click.option(
    "-t",
    "--target",
    required=True,
    help="The target cloud provider, "
    "limited to `huawei`, `alibaba`, `tencent` or `aws`."
)
def push(config, target):
    obj = CloudimgPublisher(config_file=config, target=target)
    obj.push()


@group.command(
    name="publish", help="One-click prepare, build and push cloud image."
)
@click.option(
    "-c",
    "--config",
    required=True,
    help="Path to the YAML configuration file."
)
@click.option(
    "-t",
    "--target",
    required=True,
    help="The target cloud provider, "
    "limited to `huawei`, `alibaba`, `tencent` or `aws`."
)
def publish(config, target):
    obj = CloudimgPublisher(config_file=config, target=target)
    obj.publish()
