# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Command line interface for the client.
"""

import click

from vplan.client.bootstrap import bootstrap_config, dump_instructions


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(package_name="vplan", prog_name="Vacation Plan Manager")
def vplan() -> None:
    """
    Vacation plan manager client.

    Hint: start with the bootstrap command.
    """


@vplan.command()
@click.option(
    "--force",
    "-f",
    "force",
    metavar="<force>",
    is_flag=True,
    required=False,
    default=False,
    help="Force-overwrite any files that already exist",
)
def bootstrap(force: bool) -> None:
    """
    Bootstrap local configuration.
    """
    bootstrap_config(force=force)
    dump_instructions()
