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

    Specify a path on disk for <yaml-file>, or use "-" to read from stdin.  The
    plan will be created with the name in the YAML definition.
    """


@plan.command()
@click.argument("yaml_path", metavar="<yaml-file>")
def update(yaml_path: str) -> None:
    """
    Update a plan using a YAML definition.

    Specify a path on disk for <yaml-file>, or use "-" to read from stdin.  An
    existing plan will be modified based on the name in the YAML definition.
    """


@plan.command("list")
def list_plans() -> None:
    """List all plans."""


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def delete(plan_name: str) -> None:
    """Delete a plan."""


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def status(plan_name: str) -> None:
    """Check the enabled/disabled status of a plan"""


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def enable(plan_name: str) -> None:
    """Enable a plan, allowing it to execute if the account is enabled."""


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def disable(plan_name: str) -> None:
    """Disable a plan, preventing it from executing."""


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def refresh(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def show(plan_name: str) -> None:
    """Show information about a plan."""


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
@click.option(
    "--output",
    "-o",
    "yaml_path",
    metavar="<yaml-path>",
    help="Generate output to a file rather than stdout",
)
def export(plan_name: str, yaml_path: Optional[str]) -> None:
    """
    Export a plan definition to YAML.

    YAML will be dumped to stdout unless you use the --output option to specify
    a different destination on disk.

    The resulting plan definition will be structurally equivalent to the YAML
    that was used to most recently create or modify the plan. However, the
    ordering of fields is likely to be different from your original document,
    and comments are not preserved.
    """


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
@click.option(
    "--group",
    "-g",
    "group_name",
    metavar="<group-name>",
    help="Test specific device group, by name",
)
@click.option(
    "--device",
    "-d",
    "device_path",
    metavar="<device-path>",
    help="Test specific device, in form '<room>/<device>'",
)
@click.option(
    "--auto",
    "-a",
    "auto",
    metavar="<auto>",
    is_flag=True,
    required=False,
    default=False,
    help="Advance through each test automatically",
)
@click.option(
    "--toggles",
    "-s",
    "toggles",
    metavar="<toggles>",
    required=False,
    default=2,
    type=click.INT,
    show_default=True,
    help="Number of times to toggle each device or group.",
)
def test(plan_name: str, auto: bool, toggles: int, group: Optional[str] = None, device: Optional[str] = None) -> None:
    """
    Test all devices that are a part of a plan.

    This operation cycles through all device groups, testing each one in turn,
    and waiting for your approval to start each test.  If you prefer to cycle
    through all devices without waiting for approval, use the --auto option.

    You may also test a single device group using --group and a single device
    using --device.  When testing a single device group or device, --auto is
    implied.

    A device group or device is tested by toggling it on and off several times,
    to prove that it is wired up properly and can be controlled by the plan
    engine.  Control the number of toggles using the --toggle option.
    """
