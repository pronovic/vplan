# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Main command line interface that delegates most work out to subcommands.
"""

import click

from vplan.client.commands.account import account
from vplan.client.commands.plan import plan


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(package_name="vplan", prog_name="vplan")
def vplan() -> None:
    """Manage your vacation plan in the plan engine."""


# noinspection PyTypeChecker
vplan.add_command(account)

# noinspection PyTypeChecker
vplan.add_command(plan)
