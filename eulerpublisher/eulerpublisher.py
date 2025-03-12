# coding=utf-8
import click

from eulerpublisher.container import cli as container_cli
from eulerpublisher.cloudimg import cli as cloudimg_cli
from eulerpublisher.rpm import cli as rpm_cli


@click.group()
def entrance():
    pass


def _add_commands():
    # Unified interface for extension.
    entrance.add_command(container_cli.group)
    entrance.add_command(cloudimg_cli.group)
    entrance.add_command(rpm_cli.group)


def main():
    _add_commands()
    entrance()


if __name__ == "__main__":
    main()
