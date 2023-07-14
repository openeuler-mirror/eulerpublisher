# coding=utf-8
import click

from eulerpublisher.container import cli


@click.group()
def entrance():
    pass


def _add_commands():
    # Unified interface for extension.
    entrance.add_command(cli.group)


def main():
    _add_commands()
    entrance()


if __name__ == '__main__':
    main()
