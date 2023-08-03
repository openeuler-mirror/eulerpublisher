import click

from eulerpublisher.cloudimg.aws import cli as aws_cli


@click.group(name="cloudimg", help="Commands for publishing cloud images")
def group():
    pass


# Unified interface for extension.
group.add_command(aws_cli.group)
