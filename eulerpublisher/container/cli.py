import click

from eulerpublisher.container.base import cli as base_cli
from eulerpublisher.container.app import cli as app_cli


@click.group(
    name="container",
    help="Command for publishing container images"
)
def group():
    pass


# Unified interface for extension.
group.add_command(base_cli.group)
group.add_command(app_cli.group)
