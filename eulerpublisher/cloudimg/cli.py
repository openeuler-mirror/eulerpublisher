import click

from eulerpublisher.cloudimg.gen import cli as gen_cli
from eulerpublisher.cloudimg.aws import cli as aws_cli


@click.group(name="cloudimg", help="Command for publishing cloud images")
def group():
    pass


# Unified interface for extension.
group.add_command(aws_cli.group)
group.add_command(gen_cli.group)
