# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The plan subcommand in the command line interface.
"""
import sys
from typing import Optional, Tuple

import click
from pydantic import ValidationError
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str

from vplan.client.client import (
    create_plan,
    delete_plan,
    refresh_plan,
    retrieve_all_plans,
    retrieve_plan,
    retrieve_plan_status,
    toggle_device,
    toggle_group,
    turn_off_device,
    turn_off_group,
    turn_on_device,
    turn_on_group,
    update_plan,
    update_plan_status,
)
from vplan.interface import PlanSchema, Status


def _display_plan_status(plan_name: str) -> None:
    """Display the account status."""
    result = retrieve_plan_status(plan_name)
    if not result:
        click.secho("Plan does not exist: %s" % plan_name)
    else:
        click.secho("Plan %s is %s" % (plan_name, ("enabled" if result.enabled else "disabled")))


def _read_plan_yaml(yaml_path: str) -> PlanSchema:
    """Read YAML, either from a path on disk or from stdin."""
    try:
        if yaml_path == "-":
            data = sys.stdin.read()
            result = parse_yaml_raw_as(PlanSchema, data)
        else:
            with open(yaml_path, "r", encoding="utf8") as fp:
                result = parse_yaml_raw_as(PlanSchema, fp.read())
        return result
    except ValidationError as e:
        raise click.ClickException("%s" % e) from e


def _parse_device_path(device_path: str) -> Tuple[str, str, str]:
    """Parse a device path into a tuple of (room, device, component)"""
    values = device_path.split("/", 2)
    if len(values) == 2:
        return values[0], values[1], "main"
    elif len(values) == 3:
        return values[0], values[1], values[2]
    raise click.UsageError("Device path must be either <room>/<device> or <room>/<device>/<component>")


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
    yaml = _read_plan_yaml(yaml_path)
    create_plan(yaml)
    click.secho("Created plan: %s" % yaml.plan.name)


@plan.command()
@click.argument("yaml_path", metavar="<yaml-file>")
def update(yaml_path: str) -> None:
    """
    Update a plan using a YAML definition.

    Specify a path on disk for <yaml-file>, or use "-" to read from stdin.  An
    existing plan will be modified based on the name in the YAML definition.

    When you update a plan, all existing rules at SmartThings will be removed
    and replaced with new rules.  All devices associated with those existing
    rules will be left in their current state.
    """
    yaml = _read_plan_yaml(yaml_path)
    update_plan(yaml)
    click.secho("Updated plan: %s" % yaml.plan.name)


@plan.command("list")
def list_plans() -> None:
    """List all plans."""
    for item in retrieve_all_plans():
        click.secho("%s" % item)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def delete(plan_name: str) -> None:
    """Delete a plan."""
    delete_plan(plan_name)
    click.secho("Deleted plan: %s" % plan_name)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def status(plan_name: str) -> None:
    """Check the enabled/disabled status of a plan"""
    _display_plan_status(plan_name)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def enable(plan_name: str) -> None:
    """Enable a plan, allowing it to execute if the account is enabled."""
    update_plan_status(plan_name, Status(enabled=True))
    _display_plan_status(plan_name)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def disable(plan_name: str) -> None:
    """Disable a plan, preventing it from executing."""
    update_plan_status(plan_name, Status(enabled=False))
    _display_plan_status(plan_name)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def refresh(plan_name: str) -> None:
    """Refresh the plan rules in the SmartThings infrastructure."""
    refresh_plan(plan_name)
    click.secho("Refreshed plan: %s" % plan_name)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
def show(plan_name: str) -> None:
    """Show information about a plan."""
    result = retrieve_plan(plan_name)
    if not result:
        raise click.ClickException("Plan does not exist: %s" % plan_name)
    else:
        click.secho("Schema.....: %s" % result.version)
        click.secho("Plan name..: %s" % result.plan.name)
        click.secho("Location...: %s" % result.plan.location)
        click.secho("Groups.....: %d" % len(result.plan.groups))


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
    result = retrieve_plan(plan_name)
    if not result:
        raise click.ClickException("Plan does not exist: %s" % plan_name)
    yaml = to_yaml_str(result, sort_keys=False)
    if not yaml_path:
        click.echo(yaml)
    else:
        with open(yaml_path, "w", encoding="utf8") as fp:
            fp.write(yaml)
        click.secho("Plan written to: %s" % yaml_path)


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
    help="Test specific device, in form '<room>/<device>' or '<room>/<device>/<component>'",
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
    "-t",
    "toggles",
    metavar="<toggles>",
    required=False,
    default=2,
    type=click.INT,
    show_default=True,
    help="Number of times to toggle each device or group.",
)
@click.option(
    "--delay-sec",
    "-s",
    "delay_sec",
    metavar="<delay-sec>",
    required=False,
    default=5,
    type=click.INT,
    show_default=True,
    help="Seconds to delay between each toggle",
)
def test(
    plan_name: str, auto: bool, toggles: int, delay_sec: int, group_name: Optional[str] = None, device_path: Optional[str] = None
) -> None:
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

    If you try to toggle the state too quickly, even for local Zigbee devices,
    the toggles sometimes don't work as expected.  At least a 5 second delay
    appears to work best.
    """
    if device_path is not None:
        room, device, component = _parse_device_path(device_path)
        click.secho("Testing device: %s/%s/%s" % (room, device, component))
        toggle_device(plan_name, room, device, component, toggles, delay_sec)
    elif group_name:
        click.secho("Testing group: %s" % group_name)
        toggle_group(plan_name, group_name, toggles, delay_sec)
    else:
        result = retrieve_plan(plan_name)
        if not result:
            raise click.ClickException("Plan does not exist: %s" % plan_name)
        click.secho("Testing entire plan.")
        click.secho("Toggles per device: %d" % toggles)
        click.secho("Delay between toggles: %d seconds" % delay_sec)
        click.secho("")
        for group in result.plan.groups:
            if auto:
                click.secho("Testing group: %s" % group.name)
            else:
                click.confirm("Press enter to test group %s" % group.name, show_default=False, prompt_suffix="")
            toggle_group(plan_name, group.name, toggles, delay_sec)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
@click.option(
    "--group",
    "-g",
    "group_name",
    metavar="<group-name>",
    help="Turn on specific device group, by name",
)
@click.option(
    "--device",
    "-d",
    "device_path",
    metavar="<device-path>",
    help="Test specific device, in form '<room>/<device>' or '<room>/<device>/<component>'",
)
def on(plan_name: str, group_name: Optional[str] = None, device_path: Optional[str] = None) -> None:
    """
    Turn on all devices that are part of a plan.

    You may also turn on a single device group using --group and a single
    device using --device.
    """
    if device_path is not None:
        room, device, component = _parse_device_path(device_path)
        click.secho("Turning on device: %s/%s/%s" % (room, device, component))
        turn_on_device(plan_name, room, device, component)
    elif group_name:
        click.secho("Turning on group: %s" % group_name)
        turn_on_group(plan_name, group_name)
    else:
        result = retrieve_plan(plan_name)
        if not result:
            raise click.ClickException("Plan does not exist: %s" % plan_name)
        click.secho("Turning on entire plan.")
        for group in result.plan.groups:
            turn_on_group(plan_name, group.name)


@plan.command()
@click.argument("plan_name", metavar="<plan-name>")
@click.option(
    "--group",
    "-g",
    "group_name",
    metavar="<group-name>",
    help="Turn off specific device group, by name",
)
@click.option(
    "--device",
    "-d",
    "device_path",
    metavar="<device-path>",
    help="Test specific device, in form '<room>/<device>' or '<room>/<device>/<component>'",
)
def off(plan_name: str, group_name: Optional[str] = None, device_path: Optional[str] = None) -> None:
    """
    Turn off all devices that are part of a plan.

    You may also turn off a single device group using --group and a single
    device using --device.
    """
    if device_path is not None:
        room, device, component = _parse_device_path(device_path)
        click.secho("Turning off device: %s/%s/%s" % (room, device, component))
        turn_off_device(plan_name, room, device, component)
    elif group_name:
        click.secho("Turning off group: %s" % group_name)
        turn_off_group(plan_name, group_name)
    else:
        result = retrieve_plan(plan_name)
        if not result:
            raise click.ClickException("Plan does not exist: %s" % plan_name)
        click.secho("Turning off entire plan.")
        for group in result.plan.groups:
            turn_off_group(plan_name, group.name)
