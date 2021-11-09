# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:


"""
The account subcommand in the command line interface.
"""
from typing import Optional

import click

from vplan.client.client import (
    create_account,
    delete_account,
    retrieve_account,
    retrieve_account_status,
    update_account,
    update_account_status,
)
from vplan.engine.interface import Account, Status


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
    if not token:
        token = click.prompt("Enter PAT token: ")
    result = retrieve_account()
    if result:
        result = Account(name="SmartThings", pat_token=token)
        update_account(result)
    else:
        result = Account(name="SmartThings", pat_token=token)
        create_account(result)


@account.command()
def delete() -> None:
    """Delete your account and all plans in the plan engine."""
    delete_account()
    click.secho("Account deleted")


@account.command()
def status() -> None:
    """Check the enabled/disabled status of your account."""
    result = retrieve_account_status()
    click.secho("Account is %s" % "enabled" if result.enabled else "disabled")


@account.command()
def enable() -> None:
    """Enable your account, allowing any enabled plans to execute."""
    update_account_status(Status(enabled=True))
    status()


@account.command()
def disable() -> None:
    """Disable your account, preventing all plans from executing."""
    update_account_status(Status(enabled=False))
    status()


@account.command()
def show() -> None:
    """Show the account information stored in the plan engine."""
    result = retrieve_account()
    click.secho("Account name: %s" % result.name)
    click.secho("PAT token: %s" % result.pat_token)
