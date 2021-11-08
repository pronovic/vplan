# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=unused-argument

"""
The plan subcommand in the command line interface.
"""
from typing import Optional

import click


@click.group()
@click.version_option(package_name="vplan", prog_name="vplan")
def plan() -> None:
    """Manage your vacation lighting plans in the plan engine."""


@plan.command()
@click.argument("yaml_path", metavar="<yaml-file>")
def create(yaml_path: str) -> None:
    """
    Create a new plan from a YAML definition.

    Specify a path on disk for <yaml-file>, or use "-"
    to read from stdin.  The plan will be created with
    the identifier in the YAML definition.
    """


@plan.command()
@click.argument("yaml_path", metavar="<yaml-file>")
def modify(yaml_path: str) -> None:
    """
    Modify a plan using a YAML definition.

    Specify a path on disk for <yaml-file>, or use "-"
    to read from stdin.  An existing plan will be
    modified based on the identifier in the YAML
    definition.
    """


@plan.command("list")
def list_plans() -> None:
    """List all plans."""


@plan.command()
@click.argument("plan_id", metavar="<plan-id>")
def delete(plan_id: str) -> None:
    """Delete a plan."""


@plan.command()
@click.argument("plan_id", metavar="<plan-id>")
def enable(plan_id: str) -> None:
    """Enable a plan, allowing it to execute if the account is enabled."""


@plan.command()
@click.argument("plan_id", metavar="<plan-id>")
def disable(plan_id: str) -> None:
    """Disable a plan, preventing it from executing."""


@plan.command()
@click.argument("plan_id", metavar="<plan-id>")
def refresh(plan_id: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""


@plan.command()
@click.argument("plan_id", metavar="<plan-id>")
def show(plan_id: str) -> None:
    """Show information about a plan."""


@plan.command()
@click.argument("plan_id", metavar="<plan-id>")
@click.option(
    "--output",
    "-o",
    "yaml_path",
    metavar="<yaml-path>",
    help="Generate output to a file rather than stdout",
)
def export(plan_id: str, yaml_path: Optional[str]) -> None:
    """
    Export a plan definition to YAML.

    The plan definition will be structurally equivalent to
    the YAML that was used to most recently create or modify
    the plan. However, comments and special formatting are not
    preserved.

    The YAML definition will be dumped to stdout unless you
    use the --output option to specify a destination on disk.
    """


@plan.command()
@click.argument("plan_id", metavar="<plan-id>")
@click.argument("device_name", metavar="<device-name>")
def test(plan_id: str, device_name: str) -> None:
    """
    Test a device that is part of a plan.

    The device is tested by toggling it on and off several
    times, to prove that it is wired up properly and can
    be controlled.  For instance, use this to demonstrate that
    any lamps you want to control are actually switched on.

    The <device-name> is the value specified in the plan.
    Either look in the YAML definition or run the show
    command to get a list of devices associated with the
    plan.
    """
