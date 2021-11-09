# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
The account subcommand in the command line interface.
"""

import click


@click.group()
@click.version_option(package_name="vplan", prog_name="vplan")
def account() -> None:
    """Manage your SmartThings account in the plan engine."""


@account.command("set")
@click.option(
    "--token",
    "-t",
    "token",
    metavar="<token>",
    help="Provide the token",
)
def set_account() -> None:
    """
    Set your account information in the plan engine.

    You must provide a SmartThings PAT token.  The PAT token will be used to
    interact with the SmartThings API. By default, the token is accepted
    interactively.  You may also use --token to specify it on the command line.

    Retrive a token from:

    \b
       https://account.smartthings.com/tokens

    Your PAT token requires the following scopes:

    \b
       Devices:
         List all devices (l:devices)
         See all devices (r:devices:*)
         Control all devices (x:devices:*)
    \b
       Locations
         See all locations (r:locations:*)
    \b
       Rules
         See all rules (r:rules:*)
         Manage all rules (w:rules:*)
         Control this rule (x:rules:*)
    """


@account.command()
def delete() -> None:
    """Delete your account and all plans in the plan engine."""


@account.command()
def status() -> None:
    """Check the enabled/disabled status of your account."""


@account.command()
def enable() -> None:
    """Enable your account, allowing any enabled plans to execute."""


@account.command()
def disable() -> None:
    """Disable your account, preventing all plans from executing."""


@account.command()
def show() -> None:
    """Show the account information stored in the plan engine."""
