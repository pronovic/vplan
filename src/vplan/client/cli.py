# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Main command line interface that delegates most work out to subcommands.
"""

import click

from vplan.client.client import retrieve_health, retrieve_version
from vplan.client.commands.account import account
from vplan.client.commands.plan import plan
from vplan.client.config import DEFAULT_CONFIG, set_config_path


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(package_name="vplan", prog_name="vplan")
@click.option(
    "--config",
    "-c",
    "config_path",
    metavar="<config>",
    envvar="VPLAN_CONFIG",
    default=DEFAULT_CONFIG,
    help="Path to config file on disk, or use $VPLAN_CONFIG",
)
def vplan(config_path: str) -> None:
    """Manage your vacation plan in the plan engine."""
    set_config_path(config_path)  # lazy-load config when it's needed to avoid breaking sub-command help


@vplan.command()
def check() -> None:
    """Check connectivity to the RESTful API."""
    healthy = retrieve_health()
    if not healthy:
        raise click.ClickException("Unable to connect to API")
    else:
        version = retrieve_version()
        if not version:
            raise click.ClickException("Unable to retrieve API version")
        else:
            click.echo("API is healthy, versions: %s" % version)


# noinspection PyTypeChecker
vplan.add_command(account)

# noinspection PyTypeChecker
vplan.add_command(plan)
