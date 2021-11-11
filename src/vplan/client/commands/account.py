# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:


"""
The account subcommand in the command line interface.
"""
from typing import Optional

import click

from vplan.client.client import create_or_replace_account, delete_account, retrieve_account
from vplan.engine.interface import Account


def _mask_token(token: str) -> str:
    """Mask a PAT token for display."""
    if len(token) <= 8:
        # it's not valid anyway, just show the entire thing
        return token
    else:
        return "%s%s%s" % (token[0:4], len(token[4:-4]) * "*", token[-4:])


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
def set_account(token: Optional[str]) -> None:
    """
    Set the account information stored in the plan engine.

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
    if not token:
        token = click.prompt("Enter PAT token")
    result = Account(pat_token=token)
    create_or_replace_account(result)
    click.secho("Account set")


@account.command()
def delete() -> None:
    """Delete the account information stored in the plan engine."""
    delete_account()
    click.secho("Account deleted")


@account.command()
@click.option(
    "--unmask",
    "-u",
    "unmask",
    metavar="<unmask>",
    is_flag=True,
    required=False,
    default=False,
    help="Whether to unmask the PAT token in the display",
)
def show(unmask: bool) -> None:
    """Show the account information stored in the plan engine."""
    result = retrieve_account()
    if not result:
        click.secho("Account is not set")
    else:
        token = result.pat_token if unmask else _mask_token(result.pat_token)
        click.secho("PAT token: %s" % token)
